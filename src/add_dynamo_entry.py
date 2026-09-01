import json
import logging
import os
import boto3
from shared_library import get_instance_data, resources_exist

REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()
TABLE_NAME = os.environ.get('TABLE_NAME')

dynamo_client = boto3.client('dynamodb', region_name=REGION)
sqs_client = boto3.client('sqs')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

  for record in event.get('Records', []):

    try:
      body = record.get('body', {})
      message_body = json.loads(body) if isinstance(body, str) else body
      instance_id = message_body.get('instance_id')
      cluster_name = message_body.get('cluster_name')
      if cluster_name:
        profile_role = message_body.get('profile_role')
        dynamo_client.update_item(
          TableName=TABLE_NAME,
          Key={
            'InstanceId': {'S': instance_id}
          },
          UpdateExpression="SET cluster_name = :cluster_val, profile_role = :profile_val",
          ExpressionAttributeValues={
            ':cluster_val': {'S': cluster_name},
            ':profile_val': {'S': profile_role}
          },
          ReturnValues="UPDATED_NEW"
        )
        logger.info(f"Added {cluster_name} access entry for {profile_role} to Dynamo")

      remote_sg = message_body.get('remote_sg')
      local_sg = message_body.get('local_sg')

      logger.info(f"Added to dynamo")

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
