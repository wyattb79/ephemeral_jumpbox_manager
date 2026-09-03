import json
import logging
import os
import boto3
from shared_library import get_instance_data, resources_exist

REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()
TABLE_NAME = os.environ.get('TABLE_NAME')

ec2_client = boto3.client('ec2')
dynamo_client = boto3.client('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

  for record in event.get('Records', []):

    try:
      body = record.get('body', {})
      message_body = json.loads(body) if isinstance(body, str) else body

      sns_message = message_body.get('Message')
      json_sns_message = json.loads(sns_message)

      message_detail = json_sns_message.get('detail')
      instance_id = message_detail.get('instance-id')

      logger.info(f"{instance_id} was terminated")
      response = dynamo_client.get_item(
        TableName=TABLE_NAME,
        Key={
          'InstanceId': {'S': instance_id }
        }
      )

      item = response.get('Item')
      if not item:
        logger.info(f"No Dynamo entry for {instance_id}")
        continue

      local_sg = item.get('local_sg').get('S')
      if not local_sg:
        logger.info(f"No sg access entry for {instance_id}")
        continue

      logger.info("B1")
      cluster_sg = item.get('cluster_sg').get('S')
      logger.info("B2")
      remote_sg = item.get('remote_sg').get('S')
      logger.info("B3")

      ec2_client.revoke_security_group_ingress(
        GroupId=remote_sg,
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'UserIdGroupPairs': [{'GroupId': local_sg}]
          }
        ]
      )
      logger.info("B4")

      logger.info(f"Revoking from {cluster_sg} for {local_sg} on 443")

      ec2_client.revoke_security_group_ingress(
        GroupId=cluster_sg,
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': 443,
            'ToPort': 443,
            'UserIdGroupPairs': [{'GroupId': local_sg}]
          }
        ]
      )

      logger.info(f"Revoked entries to {remote_sg} and {cluster_sg} for {local_sg} on 22/443")

      dynamo_client.update_item(
        TableName=TABLE_NAME,
        Key={
            'InstanceId': {'S': instance_id }
        },
        UpdateExpression="REMOVE #field1, #field2, #field3",
        ExpressionAttributeNames={
          "#field1": "remote_sg",
          "#field2": "local_sg",
          "#field3": "cluster_sg"
        }
      )

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
