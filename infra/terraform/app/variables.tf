# =============================================================================
# VARIABLES - Central configuration for all Spread Eagle infrastructure
# =============================================================================
# Change these values to customize your deployment.
# After changing, run: terraform apply
# =============================================================================

# -----------------------------------------------------------------------------
# GENERAL
# -----------------------------------------------------------------------------
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-2"
}

variable "project" {
  description = "Project name (used in resource names and tags)"
  type        = string
  default     = "spread-eagle"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# -----------------------------------------------------------------------------
# NETWORK
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "my_ip" {
  description = "Your public IP address for RDS access (run: curl checkip.amazonaws.com)"
  type        = string
  default     = "190.61.47.214"
}

# -----------------------------------------------------------------------------
# DATABASE (RDS)
# -----------------------------------------------------------------------------
variable "db_instance_class" {
  description = "RDS instance size (db.t4g.micro = ~$12/mo)"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Initial storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Max storage in GB (auto-scales up to this)"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Name of the default database"
  type        = string
  default     = "spread_eagle"
}

variable "db_username" {
  description = "Master username for database"
  type        = string
  default     = "postgres"
}

# -----------------------------------------------------------------------------
# S3
# -----------------------------------------------------------------------------
variable "data_bucket_name" {
  description = "S3 bucket name for data storage"
  type        = string
  default     = "spread-eagle"
}

variable "raw_data_archive_days" {
  description = "Days before moving raw data to cheaper storage"
  type        = number
  default     = 90
}

variable "raw_data_glacier_days" {
  description = "Days before moving raw data to Glacier"
  type        = number
  default     = 365
}
