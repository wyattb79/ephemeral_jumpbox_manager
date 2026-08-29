import json
import logging
import os
import boto3
from shared_library import get_instance_data, resources_exist

REGION = os.environ.get('AWS_REGION')
LOG_LEVEL = os.environ.get("LAMBDA_LOG_LEVEL", "DEBUG").upper()
JUMPBOX_TAG = os.environ.get('JUMPBOX_TAG', 'Jumpbox')
CLUSTER_TAG = os.environ.get('CLUSTER_TAG', 'Cluster')
TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

ec2_client = boto3.client('ec2')
sns_client = boto3.client('sns')

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

        payload = {
          'instance_id': instance_id,
          'remote_sg': remote_sg,
          'jumpbox_sg': jumpbox_sg
        }
        
        # Publish the JSON payload to the SNS topic
        response = sns_client.publish(
                     TopicArn=TOPIC_ARN,
                     Message=json.dumps(payload),
                     Subject='Jumpbox SecurityGroup Access'
                   )

        logger.debug(f"Publish instance_id: {instance_id} remote_sg: {remote_sg} jumpbox_sg: {jumpbox_sg} to SNS")

        # get eks cluster info, and send to sns
        if CLUSTER_TAG in flat_tags:
          cluster_name = flat_tags[CLUSTER_TAG]

          payload = {
            'cluster_name': cluster_name
          }

          # Publish the JSON payload to the SNS topic
          response = sns_client.publish(
                       TopicArn=TOPIC_ARN,
                       Message=json.dumps(payload),
                       Subject='Jumpbox Cluster Access'
                     )

          logger.debug(f"Publish cluster: {cluster_name}")
        else:
          logger.debug("No tag found for cluster")

      else:
        logger.debug(f"{instance_id} isn't tagged as a jumpbox")

    except Exception as e:
      logger.error(f"Error processing record: {e}")
      logger.error(f"Exception reason: {str(e)}")
