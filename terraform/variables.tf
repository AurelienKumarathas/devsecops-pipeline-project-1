# variables.tf — Input variable declarations for the DevSecOps demo infrastructure.
#
# This file parameterises the three configurable values in main.tf.
# In a production Terraform codebase these would be set via:
#   - terraform.tfvars (local, git-ignored)
#   - -var flags in CI/CD
#   - AWS SSM Parameter Store / Secrets Manager for sensitive values
#
# The defaults here match the values hardcoded in main.tf so the
# configuration remains deployable without any extra input.

variable "aws_region" {
  description = "AWS region to deploy resources into."
  type        = string
  default     = "eu-west-2"
}

variable "instance_type" {
  description = "EC2 instance type for the demo instance. t2.micro qualifies for AWS Free Tier."
  type        = string
  default     = "t2.micro"
}

variable "bucket_name" {
  description = "Name of the S3 bucket. Must be globally unique across all AWS accounts."
  type        = string
  default     = "devsecops-demo-bucket-vulnerable"
}
