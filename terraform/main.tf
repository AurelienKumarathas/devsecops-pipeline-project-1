# Terraform Configuration - AWS
# Hardened version: all three IaC findings from REMEDIATION.md fixed.
# Compare with main branch terraform/main.tf to see before/after.

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
# S3 Bucket
# FIX 1: All public access block flags set to true
# FIX:    KMS server-side encryption enabled
# BEFORE: block_public_acls = false (all four flags false)
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
# Security Group
# FIX 2: No wildcard 0.0.0.0/0 rules on any port
# BEFORE: ingress/egress open on all ports, all protocols
# AFTER:  ingress/egress restricted to HTTPS (443) from 10.0.0.0/8
# -------------------------------------------------------
resource "aws_security_group" "hardened_sg" {
  name        = "hardened-security-group"
  description = "Hardened security group - minimal required access only"

  ingress {
    description = "HTTPS from private network only"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    description = "HTTPS to private network only"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}

# -------------------------------------------------------
# EC2 Instance
# FIX 3: Encrypted root volume, no public IP, IMDSv2
# BEFORE: encrypted = false, public IP, hardcoded DB_PASSWORD
# Credentials are managed at runtime via Secrets Manager;
# no user_data block needed in this Terraform module.
# -------------------------------------------------------
resource "aws_instance" "hardened_instance" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  vpc_security_group_ids      = [aws_security_group.hardened_sg.id]
  associate_public_ip_address = false
  monitoring                  = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted = true
  }

  tags = {
    Name = "Hardened Instance"
  }
}
