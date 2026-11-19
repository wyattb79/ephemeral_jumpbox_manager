import json
import logging
import os
import boto3
from shared_library import resources_exist, AddAccessEntryMsgFormat

#REGION = os.environ.get('AWS_REGION')
REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()
JUMPBOX_TAG = os.environ.get('JUMPBOX_TAG')
CLUSTER_TAG = os.environ.get('CLUSTER_TAG')
SG_TAG = os.environ.get('SG_TAG')
SG_TAG_VALUE = os.environ.get('SG_TAG_VALUE')
SG_TYPE_TAG = os.environ.get('SG_TYPE_TAG')
JB_PROFILE_TAG = os.environ.get('JB_PROFILE_TAG')
TABLE_NAME = os.environ.get('TABLE_NAME')

ec2_client = boto3.client('ec2')
eks_client = boto3.client('eks')
dynamo_client = boto3.client('dynamodb', region_name=REGION)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    for record in event.get('Records', []):
        try:
            body = json.loads(record.get('body', {}))
            event_detail = body.get('detail', {})
      
            instance_id = event_detail.get('instance-id')
            logger.info(f"Instance {instance_id} started")
      
            instance_data = ec2_client.describe_instances(InstanceIds=[instance_id])
            reservations = instance_data.get('Reservations')
      
            tags = reservations[0]['Instances'][0].get('Tags')
            flattened_tags = {tag['Key']: tag['Value'] or "" for tag in tags}
            is_jumpbox = JUMPBOX_TAG in flattened_tags
      
            if is_jumpbox:
                logger.info(f"Instance {instance_id} tagged as a jumpbox")
        
                security_groups = reservations[0]['Instances'][0].get('SecurityGroups', [])
                jumpbox_sg = security_groups[0].get('GroupId')
                logger.info(f"Jumpbox has security group {jumpbox_sg}")

                logger.info(flattened_tags)

                sg_tag = flattened_tags[SG_TAG]
                logger.info(f"sg tag is {SG_TAG}")

                add_sg_entries(jumpbox_sg, sg_tag, instance_id)

                if CLUSTER_TAG in flattened_tags: 
                    cluster_name = flattened_tags[CLUSTER_TAG]
                    jumpbox_profile = flattened_tags[JB_PROFILE_TAG]
                    add_cluster_entry(cluster_name, jumpbox_profile, instance_id)

        except Exception as e:
            logger.error(f"Error processing record: {e}")
            logger.error(f"Exception reason: {str(e)}")

def add_sg_entries(jumpbox_sg, sg_tag, instance_id):
    paginator = ec2_client.get_paginator("describe_security_groups")

    pages = paginator.paginate(
        Filters=[{"Name": f"tag:{SG_TAG}", "Values": [SG_TAG_VALUE]}]
    )

    security_groups = [ sg for page in pages for sg in page["SecurityGroups"]]

    for sg in security_groups:
        sg_id = sg['GroupId']
        tags = sg.get('Tags')

        sg_type = next(tag['Value'] for tag in tags if tag['Key'] == SG_TYPE_TAG)
        logger.info(f"sg type is {sg_type}")
        if sg_type == "endpoint":
            port = 443
        elif sg_type == "ec2":
            port = 22

        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': port,
                    'ToPort': port,
                    'UserIdGroupPairs': [{'GroupId': jumpbox_sg}]
                }
            ]
        )
        logger.info(f"Added {jumpbox_sg} to {sg_id}")

        dynamo_client.put_item(
            TableName=TABLE_NAME,
            Item={
                'InstanceId': {'S': instance_id},
                'TargetId': {'S': f"securityGroup:{sg_id}"},
                'port': {'S': str(port)},
                'jumpbox_sg': {'S': jumpbox_sg}
            }
        )
        logger.info(f"Added dynamo entry for {jumpbox_sg} into {sg_id}")

def add_cluster_entry(cluster_name, jumpbox_profile, instance_id):
    logger.info(f"Attempting to add access entry for {jumpbox_profile} to {cluster_name}")

    eks_client.create_access_entry(
        clusterName=cluster_name,
        principalArn=jumpbox_profile,
        type='STANDARD'
    )
    logger.info(f"Added access entry for {jumpbox_profile} into cluster {cluster_name}")

    eks_client.associate_access_policy(
        clusterName=cluster_name,
        principalArn=jumpbox_profile,
        policyArn='arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy',
        accessScope={
        'type': 'cluster'
        }
    )
    logger.info(f"Associated admin policy for {jumpbox_profile} into cluster {cluster_name}")

    dynamo_client.put_item(
        TableName=TABLE_NAME,
        Item={
            'InstanceId': {'S': instance_id},
            'TargetId': {'S': f"cluster:{cluster_name}"},
            'JumpboxProfile': {'S': jumpbox_profile}
        }
    )
    logger.info(f"Added dynamo entry for {jumpbox_profile} into cluster {cluster_name}")
