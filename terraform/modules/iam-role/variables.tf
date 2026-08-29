variable "role_name" {
  description = "Name of the IAM role"
  type = string
}

variable "policy_arns" {
  type = map(string)
  default = {}
  description = "List of IAM Policy ARNs to attach to IAM role"
}
