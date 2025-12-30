# Spread Eagle - AWS Infrastructure

> **Status:** COMPLETE - All infrastructure deployed
> **Region:** us-east-2 (Ohio)
> **Monthly Cost Estimate:** ~$15-16/mo

---

## Quick Reference

| Resource | Value |
|----------|-------|
| **S3 Bucket** | `spread-eagle` |
| **RDS Host** | `spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com` |
| **RDS Port** | `5432` |
| **RDS Database** | `spread_eagle` |
| **RDS Username** | `postgres` |
| **Secret Name** | `spread-eagle/db` |
| **Dev IAM User** | `spread-eagle-dev` |

---

## What We Built

Spread Eagle is a sports betting analytics platform. This infrastructure supports:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                    │
│                                                                      │
│   CBB API  ──►  S3 Bucket  ──►  PostgreSQL  ──►  dbt  ──►  Dashboard│
│              (raw files)     (raw schema)    (analytics)            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

1. **Python scripts** pull college basketball data from APIs
2. **S3 bucket** stores raw JSON/CSV/Parquet files
3. **PostgreSQL** holds raw data loaded from S3
4. **dbt** transforms raw → analytics tables
5. **Dashboard** (future) visualizes betting opportunities

---

## Infrastructure Status

| Step | Resource | Status | ID/Name |
|------|----------|--------|---------|
| 1 | Terraform State (S3) | ✅ Done | `spread-eagle-tfstate` |
| 1 | Terraform Locks (DynamoDB) | ✅ Done | `spread-eagle-tf-locks` |
| 2 | Data Bucket (S3) | ✅ Done | `spread-eagle` |
| 3 | VPC | ✅ Done | `vpc-033168b57bcc2be05` |
| 3 | Public Subnet 1 | ✅ Done | `subnet-002995127a71ac013` (us-east-2a) |
| 3 | Public Subnet 2 | ✅ Done | `subnet-013c726103319d84c` (us-east-2b) |
| 3 | Internet Gateway | ✅ Done | `spread-eagle-igw` |
| 4 | RDS Security Group | ✅ Done | `sg-06025fcf87ef7bbf4` |
| 5 | RDS PostgreSQL | ✅ Done | `spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com` |
| 6 | IAM Policy (S3) | ✅ Done | `spread-eagle-s3-data-access` |
| 6 | IAM Role (Ingest) | ✅ Done | `spread-eagle-ingest-role` |
| 6 | IAM User (Dev) | ✅ Done | `spread-eagle-dev` |
| 7 | Secrets Manager | ✅ Done | `spread-eagle/db` |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud (us-east-2)                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        VPC: 10.0.0.0/16                              │   │
│  │                                                                      │   │
│  │   ┌──────────────────────┐    ┌──────────────────────┐              │   │
│  │   │  Public Subnet 1     │    │  Public Subnet 2     │              │   │
│  │   │  10.0.1.0/24         │    │  10.0.2.0/24         │              │   │
│  │   │  us-east-2a          │    │  us-east-2b          │              │   │
│  │   │                      │    │                      │              │   │
│  │   │   ┌──────────────┐   │    │                      │              │   │
│  │   │   │     RDS      │   │    │   (standby subnet    │              │   │
│  │   │   │  PostgreSQL  │   │    │    for failover)     │              │   │
│  │   │   │  spread-eagle│   │    │                      │              │   │
│  │   │   └──────────────┘   │    │                      │              │   │
│  │   └──────────────────────┘    └──────────────────────┘              │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                     ┌────────┴────────┐                                     │
│                     │ Internet Gateway │                                    │
│                     └────────┬────────┘                                     │
│                              │                                              │
│  ┌───────────────────────────┴─────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │   S3: spread-eagle          Secrets Manager        IAM              │   │
│  │   └── cbb/raw/...           └── spread-eagle/db    └── spread-eagle-│   │
│  │                                                         dev         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Port 5432 (PostgreSQL)
                                       │ Allowed IP: 190.61.47.214
                                       │
                              ┌────────┴────────┐
                              │  Your Machine   │
                              │  (Dev laptop)   │
                              └─────────────────┘
```

---

## File Structure

```
infra/
├── INFRASTRUCTURE.md          # This file - complete documentation
│
└── terraform/
    ├── bootstrap/             # Run FIRST (one-time setup)
    │   └── main.tf            # S3 + DynamoDB for Terraform state
    │
    └── app/                   # Main infrastructure
        ├── providers.tf       # AWS provider, backend config
        ├── variables.tf       # All configurable values
        ├── vpc.tf             # VPC, subnets, internet gateway
        ├── s3.tf              # Data storage bucket
        ├── security_groups.tf # Firewall rules (your IP only)
        ├── rds.tf             # PostgreSQL database
        ├── iam.tf             # Users, roles, policies
        └── secrets.tf         # Secure credential storage
```

---

## Connecting to Resources

### PostgreSQL Database

**Get credentials:**
```powershell
# From Terraform
terraform output -raw rds_password

# From Secrets Manager
aws secretsmanager get-secret-value --secret-id spread-eagle/db --query SecretString --output text --region us-east-2
```

**Connect with psql:**
```bash
psql -h spread-eagle-db.cbwyw8ky62xm.us-east-2.rds.amazonaws.com -U postgres -d spread_eagle
```

**Python connection:**
```python
import boto3
import json
import psycopg2

# Get credentials from Secrets Manager
client = boto3.client('secretsmanager', region_name='us-east-2')
secret = client.get_secret_value(SecretId='spread-eagle/db')
creds = json.loads(secret['SecretString'])

# Connect
conn = psycopg2.connect(
    host=creds['host'],
    port=creds['port'],
    database=creds['database'],
    user=creds['username'],
    password=creds['password']
)
```

### S3 Bucket

**Upload file:**
```bash
aws s3 cp data.json s3://spread-eagle/cbb/raw/
```

**List files:**
```bash
aws s3 ls s3://spread-eagle/cbb/raw/
```

**Python:**
```python
import boto3

s3 = boto3.client('s3', region_name='us-east-2')
s3.upload_file('data.json', 'spread-eagle', 'cbb/raw/data.json')
```

---

## Security Measures

| Measure | Status | Description |
|---------|--------|-------------|
| S3 encryption | ✅ | All data encrypted at rest (AES-256) |
| S3 public block | ✅ | Cannot accidentally make data public |
| S3 versioning | ✅ | Can recover deleted/overwritten files |
| RDS encryption | ✅ | Database encrypted at rest |
| RDS IP whitelist | ✅ | Only your IP (190.61.47.214) can connect |
| Secrets Manager | ✅ | DB password stored securely, not in code |
| IAM least privilege | ✅ | Minimal permissions per resource |
| Terraform state encryption | ✅ | State file encrypted in S3 |
| Terraform state locking | ✅ | DynamoDB prevents concurrent changes |

---

## Monthly Cost Estimate

| Resource | Cost | Notes |
|----------|------|-------|
| RDS db.t4g.micro | ~$12 | 24/7 runtime |
| RDS storage (20GB gp3) | ~$2 | Auto-scales to 100GB |
| S3 data bucket | ~$1 | First 50GB |
| S3 tf-state bucket | ~$0.50 | Tiny state files |
| DynamoDB | ~$0 | Pay-per-request, minimal use |
| Secrets Manager | ~$0.40 | Per secret per month |
| VPC | $0 | VPC itself is free |
| NAT Gateway | $0 | **NOT CREATED** (cost trap avoided) |
| **Total** | **~$15-16/mo** | |

### Save Money When Not Using

```powershell
# Stop RDS (saves ~$12/mo)
aws rds stop-db-instance --db-instance-identifier spread-eagle-db --region us-east-2

# Start RDS when needed
aws rds start-db-instance --db-instance-identifier spread-eagle-db --region us-east-2
```

Note: RDS auto-starts after 7 days. Set a reminder or use Lambda to keep it stopped.

---

## Common Commands

### View all Terraform outputs
```powershell
cd C:\Users\paper\Desktop\Spread_Eagle\infra\terraform\app
terraform output
```

### View sensitive values
```powershell
terraform output -raw rds_password
terraform output -raw iam_dev_access_key_id
terraform output -raw iam_dev_secret_access_key
```

### Update infrastructure
```powershell
terraform plan    # Preview changes
terraform apply   # Apply changes
```

### Update your IP address
```powershell
# 1. Get your current IP
(Invoke-WebRequest -Uri "https://checkip.amazonaws.com").Content.Trim()

# 2. Edit infra/terraform/app/variables.tf, update my_ip value

# 3. Apply
terraform apply
```

### Destroy everything (DANGER)
```powershell
# This deletes ALL infrastructure including your database!
terraform destroy
```

---

## Troubleshooting

### "Can't connect to RDS"
1. Check your IP: `(Invoke-WebRequest -Uri "https://checkip.amazonaws.com").Content.Trim()`
2. Compare to allowed IP: `terraform output allowed_ip`
3. If different, update `my_ip` in `variables.tf` and run `terraform apply`

### "Access Denied" for S3
1. Check you're using the dev user credentials
2. Verify IAM policy is attached: `aws iam list-attached-user-policies --user-name spread-eagle-dev`

### "Terraform state lock"
Someone else is running Terraform, or a previous run crashed:
```powershell
terraform force-unlock LOCK_ID
```

### "S3 bucket already exists"
Bucket names are globally unique. If someone else has it, change `data_bucket_name` in `variables.tf`.

---

## Database Schemas (for dbt)

After infrastructure is deployed, create these schemas in PostgreSQL:

```sql
-- Raw data loaded from S3
CREATE SCHEMA IF NOT EXISTS raw;

-- dbt staging models
CREATE SCHEMA IF NOT EXISTS staging;

-- dbt final analytics tables
CREATE SCHEMA IF NOT EXISTS analytics;
```

---

## Next Steps

Infrastructure is complete. Now:

1. **Configure AWS CLI** with dev user credentials
2. **Run ingest scripts** to pull CBB data to S3
3. **Load data** from S3 to PostgreSQL raw schema
4. **Set up dbt** for transformations
5. **Build analytics queries** for betting analysis
6. **Create dashboard** to visualize opportunities

---

## AWS Resource ARNs (for reference)

```
S3 Bucket:        arn:aws:s3:::spread-eagle
RDS Instance:     arn:aws:rds:us-east-2:161231034279:db:spread-eagle-db
IAM Role:         arn:aws:iam::161231034279:role/spread-eagle-ingest-role
IAM User:         arn:aws:iam::161231034279:user/spread-eagle-dev
Secret:           arn:aws:secretsmanager:us-east-2:161231034279:secret:spread-eagle/db-FF2oiJ
VPC:              arn:aws:ec2:us-east-2:161231034279:vpc/vpc-033168b57bcc2be05
Security Group:   arn:aws:ec2:us-east-2:161231034279:security-group/sg-06025fcf87ef7bbf4
```

---

*Infrastructure built step-by-step with Terraform. Last updated: Step 7 complete.*
