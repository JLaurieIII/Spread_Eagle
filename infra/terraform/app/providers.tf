# =============================================================================
# TERRAFORM CONFIGURATION
# =============================================================================
# This configures Terraform to use the S3 backend created in bootstrap.
# All state is stored remotely and locked via DynamoDB.
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "spread-eagle-tfstate"
    key            = "app/terraform.tfstate"
    region         = "us-east-2"
    dynamodb_table = "spread-eagle-tf-locks"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
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
  project     = "spread-eagle"
  environment = "dev"

  tags = {
    project     = local.project
    environment = local.environment
    managed_by  = "terraform"
  }
}
