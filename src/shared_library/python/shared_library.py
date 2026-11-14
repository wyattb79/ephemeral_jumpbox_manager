from typing import TypedDict
from botocore.exceptions import ClientError

class AddAccessEntryMsgFormat(TypedDict):
    instance_id: str
    cluster_name: str
    local_sg: str
    jumpbox_role: str

class AddSecurityGroupMsgFormat(TypedDict):
    jumpbox_sg: str
    tag: str

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
