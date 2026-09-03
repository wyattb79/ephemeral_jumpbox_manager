resource "aws_sns_topic" "ec2_shuttingdown_topic" {
  name = "ec2_shuttingdown_topic"
}

resource "aws_sns_topic_subscription" "ec2_shuttingdown_sg_subscription" {
  topic_arn = aws_sns_topic.ec2_shuttingdown_topic.arn
  protocol = "sqs"
  endpoint = module.remove_sg_access.queue_arn
}

resource "aws_sns_topic_subscription" "ec2_shuttingdown_eks_subscription" {
  topic_arn = aws_sns_topic.ec2_shuttingdown_topic.arn
  protocol = "sqs"
  endpoint = module.remove_eks_access.queue_arn
}

resource "aws_sns_topic_policy" "ec2_shuttingdown_sg_policy" {
  arn = aws_sns_topic.ec2_shuttingdown_topic.arn
  policy = data.aws_iam_policy_document.ec2_shuttingdown_sg_policy.json
}

resource "aws_sns_topic_policy" "ec2_shuttingdown_eks_policy" {
  arn = aws_sns_topic.ec2_shuttingdown_topic.arn
  policy = data.aws_iam_policy_document.ec2_shuttingdown_eks_policy.json
}

data "aws_iam_policy_document" "ec2_shuttingdown_sg_policy" {
    statement {
    sid    = "AllowEventBridgeToPublish"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    actions = [
      "sns:Publish"
    ]

    resources = [
      aws_sns_topic.ec2_shuttingdown_topic.arn
    ]
  }
}

data "aws_iam_policy_document" "ec2_shuttingdown_eks_policy" {
    statement {
    sid    = "AllowEventBridgeToPublish"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    actions = [
      "sns:Publish"
    ]

    resources = [
      aws_sns_topic.ec2_shuttingdown_topic.arn
    ]
  }
}
