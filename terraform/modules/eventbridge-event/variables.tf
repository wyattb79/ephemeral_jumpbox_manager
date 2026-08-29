variable "rule_name" {
  type = string
  description = "Name of the eventbridge rule"
}

variable "rule_description" {
  type = string
  description = "Description of the eventbridge rule"
}

variable "ec2_state" {
  type = string
  description = "Transition state of an EC2"
}

variable "target_id" {
  type = string
  description = "ID of the event target"
}

variable "queue_arn" {
  type = string
  description = "ARN of the SQS queue to send event to"
}
