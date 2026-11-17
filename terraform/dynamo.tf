resource "aws_dynamodb_table" "jumpbox_data" {
  name = "${var.dynamo_table_name}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "InstanceId"
  range_key = "TargetId"

  attribute {
    name = "InstanceId"
    type = "S"
  }

  attribute {
    name = "TargetId"
    type = "S"
  }
}
