provider "aws" {
    region = "eu-west-2"
}

data "aws_iam_role" "execution-role" {
    name = "ecsTaskExecutionRole"
}

data "aws_ecs_cluster" "c9-cluster" {
    cluster_name = "c9-ecs-cluster"
}

# create the bucket and configure its settings
resource "aws_s3_bucket" "internet-archiver-bucket" {
  bucket = "c9-internet-archiver-bucket"
  object_lock_enabled = false
}

resource "aws_s3_bucket_public_access_block" "plant-bucket-public-access" {
  bucket = aws_s3_bucket.internet-archiver-bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "internet-archiver-bucket-versioning" {
  bucket = aws_s3_bucket.internet-archiver-bucket.id
  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "internet-archiver-bucket-encryption" {
  bucket = aws_s3_bucket.internet-archiver-bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "AES256"
    }
    bucket_key_enabled = true
  }
}

# task definition for pipeline that extracts url and timestamp and uploads to RDS
resource "aws_ecs_task_definition" "internet-archiver-rds-taskdef" {
    family = "c9-internet-archiver-rds-taskdef"
    network_mode = "awsvpc"
    requires_compatibilities = ["FARGATE"]
    container_definitions = jsonencode([
        {
            name: "internet-archiver-rds"
            image: "this will contain image url when made MANUALLY"
            essential: true
            environment: [
                { name: "DB_HOST", value: var.DB_HOST },
                { name: "DB_PASSWORD", value: var.DB_PASSWORD },
                { name: "DB_USER", value: var.DB_USER }
            ]
        }
    ])
    execution_role_arn = data.aws_iam_role.execution-role.arn
    memory = 2048
    cpu = 1024
}

