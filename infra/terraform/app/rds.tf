# =============================================================================
# RDS POSTGRESQL DATABASE
# =============================================================================
# This is where your transformed data lives. dbt will write here.
#
# Instance: db.t4g.micro (~$12/mo)
# Storage: 20GB gp3, auto-scales to 100GB
# Backup: 7 days retention
# Access: Only from your IP (via security group)
#
# To stop and save money when not using:
#   aws rds stop-db-instance --db-instance-identifier spread-eagle-db --region us-east-2
#
# To start again:
#   aws rds start-db-instance --db-instance-identifier spread-eagle-db --region us-east-2
# =============================================================================

# -----------------------------------------------------------------------------
# DB SUBNET GROUP - Tells RDS which subnets it can use
# -----------------------------------------------------------------------------
resource "aws_db_subnet_group" "main" {
  name        = "${local.project}-db-subnet-group"
  description = "Subnets for RDS"
  subnet_ids  = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  tags = merge(local.tags, {
    Name = "${local.project}-db-subnet-group"
  })
}

# -----------------------------------------------------------------------------
# RANDOM PASSWORD - Auto-generate secure password
# -----------------------------------------------------------------------------
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# -----------------------------------------------------------------------------
# RDS INSTANCE - PostgreSQL database
# -----------------------------------------------------------------------------
resource "aws_db_instance" "main" {
  identifier = "${local.project}-db"

  # Engine
  engine               = "postgres"
  engine_version       = "16"
  parameter_group_name = "default.postgres16"

  # Size (small and cheap for dev)
  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"

  # Database
  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = true  # But locked to your IP via security group

  # Security
  storage_encrypted = true

  # Backups
  backup_retention_period = 7
  backup_window           = "03:00-04:00"        # 3-4 AM UTC
  maintenance_window      = "Mon:04:00-Mon:05:00" # Monday 4-5 AM UTC

  # Deletion protection (off for dev, turn on for prod)
  deletion_protection       = false
  skip_final_snapshot       = true
  delete_automated_backups  = true

  # Performance (disabled for cost savings)
  performance_insights_enabled = false

  tags = merge(local.tags, {
    Name = "${local.project}-db"
  })
}

# -----------------------------------------------------------------------------
# OUTPUTS
# -----------------------------------------------------------------------------
output "rds_endpoint" {
  description = "RDS connection endpoint (host:port)"
  value       = aws_db_instance.main.endpoint
}

output "rds_host" {
  description = "RDS hostname (without port)"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS port"
  value       = aws_db_instance.main.port
}

output "rds_database" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "rds_username" {
  description = "Database master username"
  value       = aws_db_instance.main.username
}

output "rds_password" {
  description = "Database master password (sensitive)"
  value       = random_password.db_password.result
  sensitive   = true
}
