# =============================================================================
# SECURITY GROUP - Firewall for RDS
# =============================================================================
# Only allows PostgreSQL connections from your IP address.
# If your IP changes, update my_ip in variables.tf and run terraform apply.
# =============================================================================

resource "aws_security_group" "rds" {
  name        = "${local.project}-rds-sg"
  description = "Allow PostgreSQL from my IP only"
  vpc_id      = aws_vpc.main.id

  # PostgreSQL from your IP only
  ingress {
    description = "PostgreSQL from my IP"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["${var.my_ip}/32"]
  }

  # Allow all outbound (needed for RDS to reach AWS services)
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.project}-rds-sg"
  })
}

# -----------------------------------------------------------------------------
# OUTPUTS
# -----------------------------------------------------------------------------
output "rds_security_group_id" {
  description = "Security group ID for RDS"
  value       = aws_security_group.rds.id
}

output "allowed_ip" {
  description = "IP address allowed to connect to RDS"
  value       = var.my_ip
}
