variable "python_runtime" {
  type = string
  description = "python runtime version for lambda"
}

variable "jumpbox_tag" {
  type = string
  description = "ec2 tag key to determine the ec2 is an ephemeral jumpbox"
}

variable "cluster_tag" {
  type = string
  description = "ec2 tag to determine if the jumpbox is requesting access to an EKS cluster"
}

variable "contact_email" {
  type = string
  description = "email to contact when DLQ receives a message"
}

variable "dynamo_table_name" {
  type = string
  description = "Name of the DynamoDB table for storing jumpbox information"
}

variable "sg_tag" {
  type = string
  description = "Tag used to identify security groups to have entries added"
}

variable "sg_tag_value" {
  type = string
  description = "Value of the tag used to identify security groups"
}

variable "sg_type_tag" {
  type = string
  description = "Tag used to identify the type of SG.  For EC2 we'll add ssh, for endpoint 443, etc"
}

variable "jb_profile_tag" {
    type = string
    description = "Jumpbox profile tag.  Tagged on the ec2 to save the lambda a lookup"
}
