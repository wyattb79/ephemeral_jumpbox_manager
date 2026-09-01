import json
import logging
import os
import boto3
from shared_library import get_instance_data, resources_exist

REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()
JUMPBOX_TAG = os.environ.get('JUMPBOX_TAG', 'Jumpbox')
CLUSTER_TAG = os.environ.get('CLUSTER_TAG', 'Cluster')
EKS_QUEUE_URL = os.environ.get('EKS_QUEUE_URL')
SG_QUEUE_URL = os.environ.get('SG_QUEUE_URL')

ec2_client = boto3.client('ec2')
sqs_client = boto3.client('sqs')
iam_client = boto3.client('iam')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

  for record in event.get('Records', []):
    try:
      body = json.loads(record.get('body', '{}'))
      event_detail = body.get('detail', {})

      instance_id = event_detail.get('instance-id')

      instance_data = get_instance_data(ec2_client, instance_id)

      if not instance_data:
        logger.error(f"Instance data for {instance_id} not found")
        continue

      tags = instance_data.get('Tags', [])
      flat_tags = {tag['Key']: tag.get("Value") or "" for tag in tags}

      is_jumpbox = JUMPBOX_TAG in flat_tags

      if is_jumpbox:
        # get ec2 sg info, and send to sns
        security_groups = instance_data.get('SecurityGroups', [])

        if not security_groups:
          logger.error(f"No security groups found for instance {instance_id}.")
          continue

        jumpbox_sg = security_groups[0].get('GroupId')
        if not jumpbox_sg:
          logger.error(f"Security group missing GroupId key for instance {instance_id}.")
          continue

        # Extract requested target resource ARN
        resource_arn = next((tag['Value'] for tag in tags if tag['Key'] == 'Jumpbox_Resource'), None)

        if not resource_arn or not resources_exist(resource_arn, ec2_client):
          logger.warning(f"Resource check failed for ARN '{resource_arn}' on instance {instance_id}.")
          continue

        remote_instance_id = resource_arn.split('/')[-1]
        remote_data = get_instance_data(ec2_client, remote_instance_id)
        if not remote_data or not remote_data.get('SecurityGroups'):
          logger.error(f"Remote instance {remote_instance_id} not found or missing security groups.")
          continue

        remote_sgs_list = remote_data.get('SecurityGroups', [])
        if not remote_sgs_list:
          logger.error(f"Remote instance {remote_instance_id} has an empty SecurityGroups list.")
          continue

        remote_sg = remote_sgs_list[0].get('GroupId')
        if not remote_sg:
          logger.error(f"Remote security group missing GroupId key for instance {remote_instance_id}.")
          continue

        # Publish notification to downstream SQS queue
        message_data = {
          "instance_id": instance_id,
          "remote_sg": remote_sg,
          "local_sg": jumpbox_sg,
          "sg_port": "22"
        }

        sqs_client.send_message(
          QueueUrl=SG_QUEUE_URL,
          MessageBody=json.dumps(message_data)
        )
        logger.info(f"Successfully queued update for instance {instance_id}")

        # get eks cluster info, and send to sns
        if CLUSTER_TAG in flat_tags:
          cluster_name = flat_tags[CLUSTER_TAG]

          iam_profile_data = instance_data.get('IamInstanceProfile')
          if not iam_profile_data:
            return {'statusCode': 200, 'body': f"No IAM Role attached to instance {instance_id}."}

          profile_arn = iam_profile_data['Arn']
          profile_name = profile_arn.split('/')[-1]
          iam_response = iam_client.get_instance_profile(InstanceProfileName=profile_name)
          logger.info(iam_response)
          profile_role = iam_response['InstanceProfile']['Roles'][0]['Arn']
          logger.info(profile_role)

          message_data = {
            'instance_id': instance_id,
            'cluster_name': cluster_name,
            'jumpbox_role': profile_role
          }
          sqs_client.send_message(
            QueueUrl=EKS_QUEUE_URL,
            MessageBody=json.dumps(message_data)
          )
          logger.info(f"Successfully queued update for cluster {cluster_name}")

        else:
          logger.debug("No tag found for cluster")

      else:
        logger.debug(f"{instance_id} isn't tagged as a jumpbox")

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
