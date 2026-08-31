# IAM for startup tag manager lambda
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
          "sqs:SendMessage",
        ]
        Resource = [ module.add_eks_access.queue_arn ]
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
          "iam:GetInstanceProfile"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM for add eks access lambda
module "lambda_add_eks_access_role" {
  source = "./modules/iam-role"
  role_name = "lambda_add_eks_access"
  policy_arns = {
    "lambda_add_eks_access" = aws_iam_policy.lambda_add_eks_access_policy.arn 
  }
}

resource "aws_iam_policy" "lambda_add_eks_access_policy" {
  name = "lambda_add_eks_access"

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
        Resource = [ module.add_eks_access.queue_arn ]
      },
      {
        Effect = "Allow"
        Action = [
          "eks:CreateAccessEntry"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = "*"
      }
    ]
  })
}
