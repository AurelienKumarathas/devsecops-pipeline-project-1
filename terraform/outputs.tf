# outputs.tf — Output value declarations for the DevSecOps demo infrastructure.
#
# Outputs make key resource identifiers available after `terraform apply`.
# They are consumed by:
#   - Other Terraform modules (via terraform_remote_state)
#   - CI/CD pipelines (via terraform output -raw <name>)
#   - Operators inspecting deployed resources
#
# In a production setup additional outputs would include:
#   - VPC ID, subnet IDs (for cross-module references)
#   - Security group ID (to attach to other resources)
#   - Instance public IP (for bastion/SSH access, if applicable)

output "instance_id" {
  description = "The EC2 instance ID of the deployed demo instance."
  value       = aws_instance.vulnerable_instance.id
}

output "bucket_arn" {
  description = "The ARN of the S3 demo bucket. Used to scope IAM policies."
  value       = aws_s3_bucket.vulnerable_bucket.arn
}
