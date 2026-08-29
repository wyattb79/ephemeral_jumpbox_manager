output "queue_arn" {
  description = "ARN of the SQS queue"
  value       = aws_sqs_queue.this.arn
}

output "queue_id" {
  description = "URL of the SQS queue"
  value       = aws_sqs_queue.this.id
}

output "queue_name" {
  description = "URL of the SQS queue"
  value       = aws_sqs_queue.this.name
}
