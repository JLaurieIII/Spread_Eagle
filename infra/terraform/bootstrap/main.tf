# =============================================================================
# TERRAFORM BACKEND BOOTSTRAP
# =============================================================================
# This creates the S3 bucket and DynamoDB table that Terraform uses to store
# its state. Run this ONCE, then all other Terraform uses this backend.
#
# Usage:
#   cd infra/terraform/bootstrap
#   terraform init
#   terraform apply
# =============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}

# -----------------------------------------------------------------------------
# COMMON TAGS - Applied to all resources for cost tracking
# -----------------------------------------------------------------------------
locals {
  tags = {
    project    = "spread-eagle"
    managed_by = "terraform"
    component  = "bootstrap"
  }
}

# -----------------------------------------------------------------------------
# S3 BUCKET - Stores Terraform state files
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "tf_state" {
  bucket = "spread-eagle-tfstate"
  tags   = local.tags
}

# Enable versioning - lets you recover old state if something goes wrong
resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt state files at rest - state contains sensitive info
resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block ALL public access - state files should never be public
resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket                  = aws_s3_bucket.tf_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# DYNAMODB TABLE - Prevents concurrent Terraform runs (state locking)
# -----------------------------------------------------------------------------
resource "aws_dynamodb_table" "tf_locks" {
  name         = "spread-eagle-tf-locks"
  billing_mode = "PAY_PER_REQUEST"  # Only pay when used (~$0 for light use)
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = local.tags
}

# -----------------------------------------------------------------------------
# OUTPUTS - Reference these values when configuring other Terraform
# -----------------------------------------------------------------------------
output "state_bucket_name" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.tf_state.id
}

output "lock_table_name" {
  description = "DynamoDB table for Terraform state locking"
  value       = aws_dynamodb_table.tf_locks.name
}
