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

      remote_sg = item.get('remote_sg').get('S')
      if not remote_sg:
        logger.info(f"No sg access entry for {instance_id}")
        continue

      local_sg = item.get('local_sg').get('S')

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

      logger.info(f"Revoked entry to {remote_sg} for {local_sg} on 22")

      dynamo_client.update_item(
        TableName=TABLE_NAME,
        Key={
            'InstanceId': {'S': instance_id }
        },
        UpdateExpression="REMOVE #field1, #field2",
        ExpressionAttributeNames={
          "#field1": "remote_sg",
          "#field2": "local_sg"
        }
      )

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
