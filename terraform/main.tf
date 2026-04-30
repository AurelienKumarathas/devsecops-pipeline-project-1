# Terraform Configuration - AWS
# Contains intentional security misconfigurations for IaC scanning demo.
# See REMEDIATION.md for the corrected versions of each resource.

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

# Vulnerability 1: S3 bucket with public access
# All four public access block settings are explicitly disabled.
# Any unauthenticated HTTP GET can list and download all objects.
# Trivy IaC flags this against CIS AWS Benchmark 2.1.5.
resource "aws_s3_bucket" "vulnerable_bucket" {
  bucket = "devsecops-demo-bucket-vulnerable"

  tags = {
    Name        = "Vulnerable Demo Bucket"
    Environment = "Demo"
  }
}

# BAD: All four block_public_* settings disabled
resource "aws_s3_bucket_public_access_block" "vulnerable_bucket_pab" {
  bucket = aws_s3_bucket.vulnerable_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Vulnerability 2: Security group allowing all traffic
# Ingress 0.0.0.0/0 on all ports gives any internet host access to every
# listening service on the EC2 instance — SSH, Flask API, any debug ports.
# Egress 0.0.0.0/0 on all ports allows the compromised instance to reach
# any external C2 infrastructure or exfiltration target without restriction.
# Trivy IaC flags this against CIS AWS Benchmark 5.2 and 5.3.
resource "aws_security_group" "vulnerable_sg" {
  name        = "vulnerable-security-group"
  description = "Intentionally vulnerable security group"

  # BAD: Allow all inbound traffic from any source
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # BAD: Allow all outbound traffic to any destination
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Vulnerability 3: EC2 instance with public IP, unencrypted root volume,
# and hardcoded credentials in user_data.
#
# associate_public_ip_address = true: instance is directly reachable from
# the internet without a NAT gateway or load balancer in front of it.
#
# encrypted = false on root_block_device: an EBS snapshot or physical
# media access exposes the full OS disk including any secrets written to
# disk by the application or cloud-init.
#
# Hardcoded DB_PASSWORD in user_data: EC2 instance metadata is readable
# by any process running on the instance. An SSRF vulnerability in the
# application (e.g. via the /ping endpoint) can retrieve user_data via
# http://169.254.169.254/latest/user-data, exposing the password.
# Gitleaks detects the hardcoded value in source via the hashicorp-tf-password rule.
#
# Note: ami-0b0b0b0b0b0b0b0b0 is a placeholder AMI ID for the eu-west-2
# region consistent with the configured provider. This configuration is
# intentionally not applied to real infrastructure.
resource "aws_instance" "vulnerable_instance" {
  ami           = "ami-0b0b0b0b0b0b0b0b0"  # placeholder — eu-west-2
  instance_type = "t2.micro"

  vpc_security_group_ids = [aws_security_group.vulnerable_sg.id]

  # BAD: public IP — instance directly reachable from the internet
  associate_public_ip_address = true

  # BAD: unencrypted root volume — EBS snapshot exposes full disk
  root_block_device {
    encrypted = false
  }

  # BAD: hardcoded password in user_data — readable via instance metadata endpoint
  user_data = <<-USERDATA
              #!/bin/bash
              export DB_PASSWORD="hardcoded_password"
              echo "Setting up application..."
              USERDATA

  tags = {
    Name = "Vulnerable Instance"
  }
}
