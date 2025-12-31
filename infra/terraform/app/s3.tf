# =============================================================================
# S3 DATA BUCKET
# =============================================================================
# This bucket stores all raw data pulled from APIs.
# Structure: s3://spread-eagle/cbb/raw/
# =============================================================================

resource "aws_s3_bucket" "data" {
  bucket = "spread-eagle"
  tags   = local.tags
}

# -----------------------------------------------------------------------------
# SECURITY - Encrypt data at rest
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# -----------------------------------------------------------------------------
# SECURITY - Block all public access
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# VERSIONING - Recover accidentally deleted/overwritten files
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# -----------------------------------------------------------------------------
# LIFECYCLE RULES - Move old data to cheaper storage
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  # Raw data: move to cheaper storage after 90 days
  rule {
    id     = "archive-raw-data"
    status = "Enabled"

    filter {
      prefix = "cbb/raw/"
    }

    # After 90 days -> Infrequent Access (46% cheaper)
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    # After 365 days -> Glacier (83% cheaper)
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }

  # Clean up incomplete uploads after 7 days
  rule {
    id     = "cleanup-incomplete-uploads"
    status = "Enabled"

    filter {
      prefix = ""
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# -----------------------------------------------------------------------------
# OUTPUTS
# -----------------------------------------------------------------------------
output "data_bucket_name" {
  description = "S3 bucket for data storage"
  value       = aws_s3_bucket.data.id
}

output "data_bucket_arn" {
  description = "S3 bucket ARN (for IAM policies)"
  value       = aws_s3_bucket.data.arn
}
