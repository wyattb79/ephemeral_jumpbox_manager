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
