output "event_rule_arn" {
  description = "ARN of the event rule"
  value       = aws_cloudwatch_event_rule.this.arn
}
