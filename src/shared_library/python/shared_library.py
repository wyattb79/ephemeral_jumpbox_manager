from botocore.exceptions import ClientError

def get_instance_data(ec2_client, instance_id) -> dict:
  try:
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    reservations = response.get('Reservations', [])
    if reservations and reservations[0].get('Instances'):
      return reservations[0]['Instances'][0]
  except ClientError as e:
    raise
  return {}

def resources_exist(ec2_arn: str, ec2_client) -> bool:

  if not isinstance(ec2_arn, str) or not ec2_arn:
    return False

  try:
    parts = ec2_arn.split(':')
    if len(parts) < 6:
      return False

    instance_id = parts[5].split('/')[-1]
    return bool(get_instance_data(ec2_client, instance_id))

  except Exception as e:
    return False
