module "startup_tag_manager" {
  source = "./modules/sqs-queue"
  queue_name = "startup_tag_manager"
}

module "add_eks_access" {
  source = "./modules/sqs-queue"
  queue_name = "add_eks_access"
}

module "add_sg_entry" {
  source = "./modules/sqs-queue"
  queue_name = "add_sg_entry"
}

module "add_dynamo_entry" {
  source = "./modules/sqs-queue"
  queue_name = "add_dynamo_entry"
}

module "shutdown_tag_manager" {
  source = "./modules/sqs-queue"
  queue_name = "shutdown_tag_manager"
}

resource "aws_sqs_queue_policy" "allow_eventbridge_ec2create" {
  queue_url = module.startup_tag_manager.queue_id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowEventBridge"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sqs:SendMessage"
      Resource = module.startup_tag_manager.queue_arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = module.ec2_create_event.event_rule_arn
        }
      }
    }]
  })
}
