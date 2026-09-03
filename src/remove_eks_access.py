import json
import logging
import os
import boto3
from shared_library import get_instance_data, resources_exist

REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()
TABLE_NAME = os.environ.get('TABLE_NAME')

eks_client = boto3.client('eks')
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

      cluster_name = item.get('cluster_name').get('S')
      if not cluster_name:
        logger.info(f"No EKS access entry for {instance_id}")
        continue

      profile_role = item.get('profile_role').get('S')

      eks_client.delete_access_entry(
        clusterName=cluster_name,
        principalArn=profile_role
      )

      logger.info(f"Deleted access entry for {profile_role} into cluster {cluster_name}")

      dynamo_client.update_item(
        TableName=TABLE_NAME,
        Key={
            'InstanceId': {'S': instance_id }
        },
        UpdateExpression="REMOVE #field1, #field2",
        ExpressionAttributeNames={
          "#field1": "clusterName",
          "#field2": "principalArn"
        }
      )

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
