# =============================================================================
# IAM - Identity and Access Management
# =============================================================================
# Controls WHO can do WHAT in your AWS account.
#
# We create:
# 1. Policy - defines permissions (S3 read/write)
# 2. Role - for EC2/Lambda (future Airflow, etc.)
# 3. User - for local development (your Python scripts)
# =============================================================================

# -----------------------------------------------------------------------------
# POLICY - S3 Access (read/write to data bucket)
# -----------------------------------------------------------------------------
resource "aws_iam_policy" "s3_data_access" {
  name        = "${local.project}-s3-data-access"
  description = "Read/write access to the ${local.project} S3 data bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBucket"
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = aws_s3_bucket.data.arn
      },
      {
        Sid    = "ReadWriteObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.data.arn}/*"
      }
    ]
  })

  tags = local.tags
}

# -----------------------------------------------------------------------------
# ROLE - For EC2/Lambda (future use: Airflow, scheduled jobs, etc.)
# -----------------------------------------------------------------------------
resource "aws_iam_role" "ingest" {
  name        = "${local.project}-ingest-role"
  description = "Role for ingest scripts running on EC2/Lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "ec2.amazonaws.com",
            "lambda.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.tags
}

# Attach S3 policy to role
resource "aws_iam_role_policy_attachment" "ingest_s3" {
  role       = aws_iam_role.ingest.name
  policy_arn = aws_iam_policy.s3_data_access.arn
}

# Instance profile (needed if you run on EC2)
resource "aws_iam_instance_profile" "ingest" {
  name = "${local.project}-ingest-profile"
  role = aws_iam_role.ingest.name
  tags = local.tags
}

# -----------------------------------------------------------------------------
# USER - For local development (your laptop running Python scripts)
# -----------------------------------------------------------------------------
resource "aws_iam_user" "dev" {
  name = "${local.project}-dev"
  tags = local.tags
}

# Attach S3 policy to user
resource "aws_iam_user_policy_attachment" "dev_s3" {
  user       = aws_iam_user.dev.name
  policy_arn = aws_iam_policy.s3_data_access.arn
}

# Access keys for local AWS CLI / boto3
resource "aws_iam_access_key" "dev" {
  user = aws_iam_user.dev.name
}

# -----------------------------------------------------------------------------
# OUTPUTS
# -----------------------------------------------------------------------------
output "iam_role_arn" {
  description = "IAM role ARN for ingest (use on EC2/Lambda)"
  value       = aws_iam_role.ingest.arn
}

output "iam_instance_profile" {
  description = "Instance profile for EC2"
  value       = aws_iam_instance_profile.ingest.name
}

output "iam_dev_user" {
  description = "IAM user for local development"
  value       = aws_iam_user.dev.name
}

output "iam_dev_access_key_id" {
  description = "Access key ID for dev user (use in ~/.aws/credentials)"
  value       = aws_iam_access_key.dev.id
  sensitive   = true
}

output "iam_dev_secret_access_key" {
  description = "Secret access key for dev user (use in ~/.aws/credentials)"
  value       = aws_iam_access_key.dev.secret
  sensitive   = true
}
