resource "aws_cloudwatch_event_rule" "this" {
  name = var.rule_name
  description = var.rule_description

  event_pattern = jsonencode({
    source = ["aws.ec2"]
    detail-type = ["EC2 Instance State-change Notification"]
    detail = {
      "state" = [var.ec2_state]
    }
  })
}

resource "aws_cloudwatch_event_target" "this" {
  rule = aws_cloudwatch_event_rule.this.name
  target_id = var.target_id
  arn = var.queue_arn
}
