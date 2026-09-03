import json
import logging
import os
import boto3
from shared_library import get_instance_data, resources_exist

REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()
DYNAMO_QUEUE = os.environ.get("DYNAMO_QUEUE")

ec2_client = boto3.client('ec2')
sqs_client = boto3.client('sqs')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

  for record in event.get('Records', []):

    try:
      body = record.get('body', {})
      message_body = json.loads(body) if isinstance(body, str) else body
      instance_id = message_body.get('instance_id')
      remote_sg = message_body.get('remote_sg')
      local_sg = message_body.get('local_sg')
      sg_port = message_body.get('sg_port')

      ec2_client.authorize_security_group_ingress(
        GroupId=remote_sg,
        IpPermissions=[
          {
            'IpProtocol': 'tcp',
            'FromPort': int(sg_port),
            'ToPort': int(sg_port),
            'UserIdGroupPairs': [{'GroupId': local_sg}]            
          }
        ]
      )

      logger.info(f"Added entry to {remote_sg} for {local_sg} on {sg_port}")

      # Publish notification to downstream SQS queue
      message_data = {
        "instance_id": instance_id,
        "remote_sg": remote_sg,
        "local_sg": local_sg
      }

      sqs_client.send_message(
        QueueUrl=DYNAMO_QUEUE,
        MessageBody=json.dumps(message_data)
      )

      logger.info(f"Queued for SG into {DYNAMO_QUEUE}")

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
