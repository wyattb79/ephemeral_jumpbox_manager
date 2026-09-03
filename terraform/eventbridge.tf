module "ec2_create_event" {
  source = "./modules/eventbridge-event"
  rule_name = "ec2-creation"
  rule_description = "Generate event for EC2 running"
  ec2_state = "running"
  resource_arn = module.startup_tag_manager.queue_arn
  target_id = "EC2-create" 
}

module "ec2_shuttingdown_event" {
  source = "./modules/eventbridge-event"
  rule_name = "ec2-shuttingdown"
  rule_description = "Generate event for EC2 shutting-down"
  ec2_state = "shutting-down"
  resource_arn = resource.aws_sns_topic.ec2_shuttingdown_topic.arn
  target_id = "EC2-shuttingdown" 
}
