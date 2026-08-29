data "archive_file" "this" {
  type = "zip"
  source_file = "${path.root}/../src/${var.function_name}.py"
  output_path = "${path.root}/../src/${var.function_name}.zip"
}

resource "aws_lambda_function" "this" {
  filename = data.archive_file.this.output_path
  function_name = var.function_name
  role = var.role
  runtime = var.python_runtime
  handler = "${var.function_name}.handler"

  timeout = 30

  environment {
    variables = var.lambda_env_vars
  }

  layers = var.layers
}

resource "aws_lambda_event_source_mapping" "this" {
  event_source_arn = var.queue_arn
  function_name = aws_lambda_function.this.arn
  batch_size = 1
  enabled = true

  function_response_types = ["ReportBatchItemFailures"]
}
