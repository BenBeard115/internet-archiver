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


# create a role for the EventBridge schedule
resource "aws_iam_role" "schedule-role" {
    name = "c9-internet-archiver-schedule-role"
    assume_role_policy = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "scheduler.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": "129033205317"
                    }
                }
            }
        ]
    })
}

# create policy for the schedule role
resource "aws_iam_policy" "schedule-policy" {
    name        = "c9-internet-archiver-terraform-schedule-policy"
    policy = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecs:RunTask",
                    "states:StartExecution"
                ],
                "Resource": [
                    "${aws_ecs_task_definition.EXAMPLE-TASK-DEF-NAME.arn}"
                ],
                "Condition": {
                    "ArnLike": {
                        "ecs:cluster": "${data.aws_ecs_cluster.c9-cluster.arn}"
                    }
                }
            },
            {
                "Effect": "Allow",
                "Action": "iam:PassRole",
                "Resource": [
                    "*"
                ],
                "Condition": {
                    "StringLike": {
                        "iam:PassedToService": "ecs-tasks.amazonaws.com"
                    }
                }
            }
        ]
    })
}

# attach policy to schedule role
resource "aws_iam_policy_attachment" "schedule-policy-attachment" {
    name = "c9-internet-archiver-schedule-policy-attachment"
    roles = [aws_iam_role.schedule-role.name]
    policy_arn = aws_iam_policy.schedule-policy.arn
}

# create EventBridge schedule for web scraper script
resource "aws_scheduler_schedule" "internet-archiver-scraper-schedule" {
    name       = "c9-internet-archiver-scraper-schedule"
    schedule_expression = "cron(0 9-18/3 * * ? *)"
    flexible_time_window {
        mode = "OFF"
    }
    target {
        arn      = data.aws_ecs_cluster.c9-cluster.arn
        role_arn = aws_iam_role.schedule-role.arn
        ecs_parameters {
          task_definition_arn = aws_ecs_task_definition.EXAMPLE-TASK-DEF-NAME.arn
          task_count = 1
          launch_type = "FARGATE"
          platform_version = "LATEST"
          network_configuration {
            subnets = [ "subnet-0d0b16e76e68cf51b", "subnet-081c7c419697dec52", "subnet-02a00c7be52b00368" ]
            security_groups = [ "sg-020697b6514174b72" ]
            assign_public_ip = true
          }
        }
    }
}



# Creates the security group allowing postgres access
resource "aws_security_group" "c9-internet-archiver-database-sg" {
  name        = "c9-internet-archiver-database-sg"
  description = "Allow inbound postgres traffic"
  vpc_id      = var.VPC_ID

  ingress {
    description      = "Postgres access"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

# Creates the postgres database
resource "aws_db_instance" "c9_internet_archiver_database" {
  allocated_storage             = 10
  db_name                       = "c9_internet_archiver_database"
  identifier                    = "c9-internet-archiver-terraform"
  engine                        = "postgres"
  engine_version                = "15.3"
  instance_class                = "db.t3.micro"
  publicly_accessible           = true 
  performance_insights_enabled  = false
  skip_final_snapshot           = true
  db_subnet_group_name          = "public_subnet_group"
  vpc_security_group_ids        = [aws_security_group.c9-internet-archiver-database-sg.id]
  username                      = var.DB_USERNAME
  password                      = var.DB_PASSWORD
}
