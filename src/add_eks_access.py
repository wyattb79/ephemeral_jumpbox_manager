import json
import logging
import os
import boto3
from shared_library import get_instance_data, resources_exist

REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()

eks_client = boto3.client('eks')
sqs_client = boto3.client('sqs')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

  for record in event.get('Records', []):

    try:
      body = record.get('body', {})
      message_body = json.loads(body) if isinstance(body, str) else body
      cluster_name = message_body.get('cluster_name')
      jumpbox_profile = message_body.get('jumpbox_role')
      logger.info(f"Got instance profile {jumpbox_profile} for cluster {cluster_name}")
      eks_client.create_access_entry(
        clusterName=cluster_name,
        principalArn=jumpbox_profile,
        type='EC2_LINUX'
      )
      logger.info(f"Added access entry for {jumpbox_profile} into cluster {cluster_name}")

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
