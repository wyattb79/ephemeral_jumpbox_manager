import json
import logging
import os
import boto3
from shared_library import resources_exist

REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()
TABLE_NAME = os.environ.get('TABLE_NAME')

eks_client = boto3.client('eks')
dynamo_client = boto3.client('dynamodb')

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

def handler(event, context):

  logger.info("Lambda started")

  for record in event.get('Records', []):

    try:
      body = record.get('body', {})
      message_body = json.loads(body) if isinstance(body, str) else body

      sns_message = message_body.get('Message')
      json_sns_message = json.loads(sns_message)

      message_detail = json_sns_message.get('detail')
      instance_id = message_detail.get('instance-id')

      logger.info(f"{instance_id} was terminated")

      response = dynamo_client.query(
        TableName=TABLE_NAME,
        KeyConditionExpression="InstanceId = :inst_id AND begins_with(TargetId, :prefix)",
        ExpressionAttributeValues={
            ":inst_id": {"S":instance_id},
            ":prefix": {"S": "cluster:"},
        }
      )

      items = response.get('Items')
      if not items:
        logger.info(f"No Dynamo entry for {instance_id}")
        continue

      item = items[0]

      cluster_name = item.get('TargetId').get('S')
      cluster_name.remove_prefix("cluster:")
      if not cluster_name:
        logger.info(f"No EKS access entry for {instance_id}")
        continue

      jumpbox_profile = item.get('jumpbox_profile').get('S')

      eks_client.delete_access_entry(
        clusterName=cluster_name,
        principalArn=jumpbox_profile
      )

      logger.info(f"Deleted access entry for {jumpbox_profile} into cluster {cluster_name}")

      dynamo_client.delete_item(
        TableName=TABLE_NAME,
        Key={
            'InstanceId': {'S': instance_id },
            'TargetType': {'S': "cluster" },
            'ClusterName': {'S': cluster_name }
        }
      )

      response = dynamo_client.query(
        TableName=TABLE_NAME,
        KeyConditionExpression="InstanceId = :inst_val",
        ExpressionAttributeValues={
          ":inst_val": {"S": instance_id}
        }
      )
      items = response.get("Items")
      for item in items:
        sg_id = item["TargetId"]["S"]
        port = item["port"]["S"]
        jumpbox_sg = item["jumpbox_sg"]["S"]

        ec2_client.revoke_security_group_ingress(
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
        logger.info(f"Removed {jumpbox_sg} to {sg_id}")

        dynamo_client.delete_item(
            TableName=TABLE_NAME,
            Key={
                'InstanceId': {'S': instance_id },
                'TargetType': {'S': "securityGroup" },
                'TargetId': {'S': sg_id }
            }
        )
        logger.info(f"Removed dynamo entry for {sg_id} access from {instance_id}")

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
