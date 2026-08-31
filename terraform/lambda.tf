# function to pull out relevant tags and pass them to appropriate queues
module "lambda_startup_tag_manager" {
  source = "./modules/lambda-function"
  function_name = "startup_tag_manager"
  role = module.lambda_startup_tag_manager_role.role_arn
  region = data.aws_region.current.region
  python_runtime = var.python_runtime

  lambda_env_vars = {
    JUMPBOX_TAG = var.jumpbox_tag,
    CLUSTER_TAG = var.cluster_tag,
    REGION = data.aws_region.current.region
    EKS_QUEUE_URL = module.add_eks_access.queue_name
#    SG_QUEUE_URL = module
  }

  queue_arn = module.startup_tag_manager.queue_arn

  layers = [aws_lambda_layer_version.shared_library.arn]
}

# function to allow access to EKS
module "lambda_add_eks_access" {
  source = "./modules/lambda-function"
  function_name = "add_eks_access"
  role = module.lambda_add_eks_access_role.role_arn
  region = data.aws_region.current.region
  python_runtime = var.python_runtime

  lambda_env_vars = {
    JUMPBOX_TAG = var.jumpbox_tag,
    CLUSTER_TAG = var.cluster_tag,
    REGION = data.aws_region.current.region
  }

  queue_arn = module.add_eks_access.queue_arn

  layers = [aws_lambda_layer_version.shared_library.arn]
}

# shared library
data "archive_file" "shared_library" {
  type = "zip"
  source_dir = "${path.module}/../src/shared_library"
  output_path = "${path.module}/files/shared_library.zip"
}

resource "aws_lambda_layer_version" "shared_library" {
  filename = data.archive_file.shared_library.output_path
  layer_name = "shared_library"
  source_code_hash = data.archive_file.shared_library.output_base64sha256
  compatible_runtimes = [var.python_runtime]

  description = "Shared library for lambdas"
}
