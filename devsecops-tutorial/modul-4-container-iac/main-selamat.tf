# Versi yang lebih selamat bagi terraform/main.tf. JANGAN jalankan `terraform apply`.
# Letak sebagai terraform/main.tf (gantikan fail asal) untuk membandingkan hasil imbasan.
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-1"
}

variable "cidr_admin" {
  description = "Julat IP rangkaian admin yang dibenarkan SSH"
  type        = string
  default     = "203.0.113.0/24"
}

variable "cidr_vpc" {
  description = "Julat IP VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "kunci_kms" {
  description = "ARN kunci KMS untuk penyulitan"
  type        = string
  default     = "arn:aws:kms:ap-southeast-1:111122223333:key/contoh"
}

# Kata laluan DB datang dari luar kod (secret store atau pemboleh ubah persekitaran TF_VAR_kata_laluan_db)
variable "kata_laluan_db" {
  description = "Kata laluan pangkalan data"
  type        = string
  sensitive   = true
}

resource "aws_s3_bucket" "muat_naik" {
  bucket = "kedai-bengkel-muat-naik"
}

# Tiada akses awam
resource "aws_s3_bucket_public_access_block" "muat_naik" {
  bucket                  = aws_s3_bucket.muat_naik.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "muat_naik" {
  bucket = aws_s3_bucket.muat_naik.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kunci_kms
    }
  }
}

resource "aws_s3_bucket_versioning" "muat_naik" {
  bucket = aws_s3_bucket.muat_naik.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_security_group" "web" {
  name        = "kedai-web"
  description = "Kumpulan keselamatan web"

  ingress {
    description = "SSH daripada rangkaian admin sahaja"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.cidr_admin]
  }

  # Web awam mesti boleh dicapai daripada internet; pengecualian ini diterima dengan alasan.
  #trivy:ignore:AWS-0107
  ingress {
    description = "HTTPS awam"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Trafik keluar dalam VPC sahaja"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.cidr_vpc]
  }
}

resource "aws_db_instance" "utama" {
  identifier                          = "kedai-db"
  engine                              = "mysql"
  instance_class                      = "db.t3.micro"
  allocated_storage                   = 20
  username                            = "kedai_app"
  password                            = var.kata_laluan_db
  publicly_accessible                 = false
  storage_encrypted                   = true
  kms_key_id                          = var.kunci_kms
  backup_retention_period             = 7
  deletion_protection                 = true
  skip_final_snapshot                 = false
  final_snapshot_identifier           = "kedai-db-akhir"
  iam_database_authentication_enabled = true
  vpc_security_group_ids              = [aws_security_group.web.id]
}
