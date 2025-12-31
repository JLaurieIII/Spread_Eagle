# =============================================================================
# SECRETS MANAGER - Secure credential storage
# =============================================================================
# Stores database credentials securely. Your Python scripts fetch these at
# runtime instead of hardcoding passwords in code or .env files.
#
# To retrieve in Python:
#   import boto3
#   import json
#   client = boto3.client('secretsmanager', region_name='us-east-2')
#   secret = client.get_secret_value(SecretId='spread-eagle/db')
#   creds = json.loads(secret['SecretString'])
#   # creds['host'], creds['password'], etc.
# =============================================================================

# -----------------------------------------------------------------------------
# SECRET - Database credentials
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "db" {
  name        = "${local.project}/db"
  description = "PostgreSQL database credentials for ${local.project}"

  # For dev: no recovery window (can delete immediately)
  # For prod: set to 7-30 days
  recovery_window_in_days = 0

  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id

  secret_string = jsonencode({
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    database = aws_db_instance.main.db_name
    username = aws_db_instance.main.username
    password = random_password.db_password.result
    # Convenience: full connection URL
    url      = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
  })
}

# -----------------------------------------------------------------------------
# IAM POLICY - Allow reading secrets
# -----------------------------------------------------------------------------
resource "aws_iam_policy" "secrets_read" {
  name        = "${local.project}-secrets-read"
  description = "Allow reading secrets from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadSecrets"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.db.arn
      }
    ]
  })

  tags = local.tags
}

# Attach to ingest role (for EC2/Lambda)
resource "aws_iam_role_policy_attachment" "ingest_secrets" {
  role       = aws_iam_role.ingest.name
  policy_arn = aws_iam_policy.secrets_read.arn
}

# Attach to dev user (for local development)
resource "aws_iam_user_policy_attachment" "dev_secrets" {
  user       = aws_iam_user.dev.name
  policy_arn = aws_iam_policy.secrets_read.arn
}

# -----------------------------------------------------------------------------
# OUTPUTS
# -----------------------------------------------------------------------------
output "db_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db.arn
}

output "db_secret_name" {
  description = "Name of the database credentials secret"
  value       = aws_secretsmanager_secret.db.name
}
