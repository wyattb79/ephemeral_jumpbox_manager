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
          "sqs:SendMessage",
        ]
        Resource = [ module.add_sg_entry.queue_arn ]
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
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
        ]
        Resource = [ module.add_dynamo_entry.queue_arn ]
      },
    ]
  })
}

# IAM for add security group entry lambda
module "lambda_add_sg_entry_role" {
  source = "./modules/iam-role"
  role_name = "lambda_add_sg_entry"
  policy_arns = {
    "lambda_add_sg_entry" = aws_iam_policy.lambda_add_sg_entry_policy.arn 
  }
}

resource "aws_iam_policy" "lambda_add_sg_entry_policy" {
  name = "lambda_add_sg_entry"

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
        Resource = [ module.add_sg_entry.queue_arn ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:AuthorizeSecurityGroupIngress",
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM for add dynamo entry lambda
module "lambda_add_dynamo_entry_role" {
  source = "./modules/iam-role"
  role_name = "lambda_add_dynamo_entry"
  policy_arns = {
    "lambda_add_dynamo_entry" = aws_iam_policy.lambda_add_dynamo_entry_policy.arn 
  }
}

resource "aws_iam_policy" "lambda_add_dynamo_entry_policy" {
  name = "lambda_add_dynamo_entry"

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
        Resource = [ module.add_dynamo_entry.queue_arn ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem"
        ]
        Resource: [ "arn:aws:dynamodb:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:table/${var.dynamo_table_name}",
        "arn:aws:dynamodb:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:table/${var.dynamo_table_name}/index/*"
        ]
      },
    ]
  })
}
