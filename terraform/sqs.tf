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

module "remove_sg_access" {
  source = "./modules/sqs-queue"
  queue_name = "remove_sg_access"
}

module "remove_eks_access" {
  source = "./modules/sqs-queue"
  queue_name = "remove_eks_access"
}

resource "aws_sqs_queue_policy" "allow_eventbridge_ec2create" {
  queue_url = module.startup_tag_manager.queue_url

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

resource "aws_sqs_queue_policy" "allow_sns_sg_ec2terminate" {
  queue_url = module.remove_sg_access.queue_url

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowSNS"
      Effect = "Allow"
      Principal = {
        Service = "sns.amazonaws.com"
      }
      Action = "sqs:SendMessage"
      Resource = module.remove_sg_access.queue_arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = resource.aws_sns_topic.ec2_shuttingdown_topic.arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue_policy" "allow_sns_eks_ec2terminate" {
  queue_url = module.remove_eks_access.queue_url

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Sid = "AllowSNS"
      Effect = "Allow"
      Principal = {
        Service = "sns.amazonaws.com"
      }
      Action = "sqs:SendMessage"
      Resource = module.remove_eks_access.queue_arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = resource.aws_sns_topic.ec2_shuttingdown_topic.arn
        }
      }
    }]
  })
}
