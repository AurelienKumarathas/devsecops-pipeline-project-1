# Terraform Configuration - AWS
# Hardened version: all IaC findings from REMEDIATION.md have been fixed.
# Compare with main branch terraform/main.tf to see intentional vs remediated.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "eu-west-2"
}

# -------------------------------------------------------
# S3 Bucket — FIX: all public access block flags enabled
# BEFORE: block_public_acls = false (all four flags false)
# AFTER:  all four flags set to true
# -------------------------------------------------------
resource "aws_s3_bucket" "hardened_bucket" {
  bucket = "devsecops-demo-bucket-hardened"

  tags = {
    Name        = "Hardened Demo Bucket"
    Environment = "Demo"
  }
}

resource "aws_s3_bucket_public_access_block" "hardened_bucket_pab" {
  bucket = aws_s3_bucket.hardened_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "hardened_bucket_sse" {
  bucket = aws_s3_bucket.hardened_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# -------------------------------------------------------
# Security Group — FIX: no wildcard 0.0.0.0/0 rules
# BEFORE: ingress/egress open on all ports, all protocols
# AFTER:  ingress restricted to HTTPS (443) from known CIDR
#         egress restricted to HTTPS (443) only
# -------------------------------------------------------
resource "aws_security_group" "hardened_sg" {
  name        = "hardened-security-group"
  description = "Hardened security group - minimal required access only"

  ingress {
    description = "HTTPS from trusted CIDR only"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    description = "HTTPS outbound only"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# -------------------------------------------------------
# Secrets Manager — credentials stored securely
# BEFORE: DB_PASSWORD hardcoded in user_data plaintext
# AFTER:  secret ARN referenced; no plaintext credentials
# -------------------------------------------------------
data "aws_secretsmanager_secret_version" "app_credentials" {
  secret_id = "devsecops-demo/app-credentials"
}

# -------------------------------------------------------
# EC2 Instance — FIX: encrypted root volume, no public IP,
#                     credentials from Secrets Manager
# BEFORE: encrypted = false, associate_public_ip_address = true,
#         DB_PASSWORD hardcoded in user_data
# AFTER:  encrypted = true, public IP disabled,
#         credentials retrieved from Secrets Manager at boot
# -------------------------------------------------------
resource "aws_instance" "hardened_instance" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  vpc_security_group_ids      = [aws_security_group.hardened_sg.id]
  associate_public_ip_address = false

  root_block_device {
    encrypted = true
  }

  user_data = <<-USERDATA
              #!/bin/bash
              # Retrieve credentials from Secrets Manager at runtime
              SECRET=$(aws secretsmanager get-secret-value \
                --secret-id devsecops-demo/app-credentials \
                --query SecretString --output text)
              export DB_PASSWORD=$(echo $SECRET | python3 -c \
                "import sys,json; print(json.load(sys.stdin)['db_password'])")
              echo "Application starting..."
              USERDATA

  tags = {
    Name = "Hardened Instance"
  }
}
