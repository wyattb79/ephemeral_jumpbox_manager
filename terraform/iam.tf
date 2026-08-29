module "lambda_startup_tag_manager_role" {
  source = "./modules/iam-role"
  role_name = "lambda_startup_tag_manager"
  policy_arns = {
    "lambda_startup_tag_manager" = aws_iam_policy.lambda_startup_tag_manager_policy.arn 
  }
}

resource "aws_iam_policy" "lambda_startup_tag_manager_policy" {
  name = "lambda_pull_ec2_tags"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = [ module.startup_tag_manager.queue_arn ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = "arn:aws:sns:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:${aws_sns_topic.ec2_created_tags_topic.name}"
      },
    ]
  })
}
