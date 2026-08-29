variable "function_name" {
  type = string
  description = "Name of the lambda"
}

variable "role" {
  type = string
  description = "Execution role for the function"
}

variable "region" {
  type = string
  description = "Current region"
}

variable "python_runtime" {
  type = string
  description = "Python runtime"
}

variable "lambda_env_vars" {
  type = map(string)
  description = "Map of environment variables for the lambda"
  default = {}
}

variable "queue_arn" {
  type = string
  description = "ARN of the queue of events that triggers the lambda"
  default = ""
}

variable "layers" {
  type = list(string)
  description = "Shared library layers"
}
