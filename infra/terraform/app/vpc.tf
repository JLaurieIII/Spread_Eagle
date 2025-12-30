# =============================================================================
# VPC - Virtual Private Cloud
# =============================================================================
# A private network for your AWS resources. RDS requires subnets in at least
# 2 availability zones, so we create 2 public subnets.
#
# NO NAT GATEWAY - that's an easy $35+/mo mistake. We use public subnets only.
# =============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, {
    Name = "${local.project}-vpc"
  })
}

# -----------------------------------------------------------------------------
# SUBNETS - 2 public subnets in different AZs (required by RDS)
# -----------------------------------------------------------------------------
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-2a"
  map_public_ip_on_launch = true

  tags = merge(local.tags, {
    Name = "${local.project}-public-1"
  })
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-2b"
  map_public_ip_on_launch = true

  tags = merge(local.tags, {
    Name = "${local.project}-public-2"
  })
}

# -----------------------------------------------------------------------------
# INTERNET GATEWAY - Allows resources to reach the internet
# -----------------------------------------------------------------------------
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.tags, {
    Name = "${local.project}-igw"
  })
}

# -----------------------------------------------------------------------------
# ROUTE TABLE - Directs traffic to the internet gateway
# -----------------------------------------------------------------------------
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.tags, {
    Name = "${local.project}-public-rt"
  })
}

# Associate route table with both subnets
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# -----------------------------------------------------------------------------
# OUTPUTS
# -----------------------------------------------------------------------------
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs (for RDS subnet group)"
  value       = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}
