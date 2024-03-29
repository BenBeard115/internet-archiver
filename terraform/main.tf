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

resource "aws_s3_bucket_public_access_block" "internet-archiver-bucket-public-access" {
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

# task definition for pipeline that extracts non duplicate from S3 and rescrapes them
resource "aws_ecs_task_definition" "c9-internet-archiver-auto-scraper-taskdef" {
    family = "c9-internet-archiver-auto-scraper-taskdef"
    network_mode = "awsvpc"
    requires_compatibilities = ["FARGATE"]
    container_definitions = jsonencode([
        {
            name: "c9-internet-archiver-auto-scraper"
            image: "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c9-internet-archiver-auto-scraper:latest"
            essential: true
            environment: [
                { name: "S3_BUCKET", value: var.S3_BUCKET },
                { name: "DB_IP", value: var.DB_IP },
                { name: "DB_PORT", value: var.DB_PORT },
                { name: "DB_NAME", value: var.DB_NAME },
                { name: "DB_USERNAME", value: var.DB_USERNAME },
                { name: "DB_PASSWORD", value: var.DB_PASSWORD },
                { name: "AWS_ACCESS_KEY_ID", value: var.AWS_ACCESS_KEY_ID },
                { name: "AWS_SECRET_ACCESS_KEY", value: var.AWS_SECRET_ACCESS_KEY },
                { name: "URL_TABLE_NAME", value: var.URL_TABLE_NAME },
                { name: "SCRAPE_TABLE_NAME", value: var.SCRAPE_TABLE_NAME }

                
            ],
            "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": var.AWS_GROUP,
                "awslogs-region": var.AWS_REGION,
                "awslogs-stream-prefix": var.AWS_STREAM_PREFIX,
                "awslogs-create-group": "true"
            }
        }
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
                    "${aws_ecs_task_definition.c9-internet-archiver-auto-scraper-taskdef.arn}"
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
resource "aws_scheduler_schedule" "c9-internet-archiver-scraper-schedule" {
    name       = "c9-internet-archiver-scraper-schedule"
    schedule_expression = "cron(0 */3 * * ? *)"
    flexible_time_window {
        mode = "OFF"
    }
    target {
        arn      = data.aws_ecs_cluster.c9-cluster.arn
        role_arn = aws_iam_role.schedule-role.arn
        ecs_parameters {
          task_definition_arn = aws_ecs_task_definition.c9-internet-archiver-auto-scraper-taskdef.arn
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
  identifier                    = "c9-internet-archiver"
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

# task definition for dashboard
resource "aws_ecs_task_definition" "c9-internet-archiver-dashboard-taskdef" {
    family = "c9-internet-archiver-dashboard-taskdef"
    network_mode = "awsvpc"
    requires_compatibilities = ["FARGATE"]
    container_definitions = jsonencode([
        {
            name: "c9-internet-archiver-dashboard"
            image: "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c9-internet-archiver-dashboard:latest"
            essential: true
            portMappings: [{
                containerPort = 8501
                hostPort = 8501
            }]
            environment: [
                { name: "DB_IP", value: var.DB_IP },
                { name: "DB_PORT", value: var.DB_PORT },
                { name: "DB_NAME", value: var.DB_NAME },
                { name: "DB_USERNAME", value: var.DB_USERNAME},
                { name: "DB_PASSWORD", value: var.DB_PASSWORD },
                { name: "AWS_ACCESS_KEY_ID", value: var.AWS_ACCESS_KEY_ID },
                { name: "AWS_SECRET_ACCESS_KEY", value: var.AWS_SECRET_ACCESS_KEY }
            ],
            "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": var.AWS_GROUP,
                "awslogs-region": var.AWS_REGION,
                "awslogs-stream-prefix": var.AWS_STREAM_PREFIX,
                "awslogs-create-group": "true"
            }
        }
    }
    ])
    execution_role_arn = data.aws_iam_role.execution-role.arn
    memory = 2048
    cpu = 1024
}

# security group to allow inbound traffic on port 8501 for the dashboard
resource "aws_security_group" "c9-internet-archiver-dashboard-securitygroup" {
  name        = "c9-internet-archiver-dashboard-securitygroup"
  description = "Allow inbound traffic for port 8501, so users can see the dashboard"
  vpc_id      = "vpc-04423dbb18410aece"

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# start ECS service for the dashboard
resource "aws_ecs_service" "c9-internet-archiver-dashboard-service" {
    name = "c9-internet-archiver-dashboard-service"
    cluster = data.aws_ecs_cluster.c9-cluster.id
    task_definition = aws_ecs_task_definition.c9-internet-archiver-dashboard-taskdef.arn
    desired_count = 1
    launch_type = "FARGATE"
    network_configuration {
      subnets = ["subnet-0d0b16e76e68cf51b", "subnet-081c7c419697dec52", "subnet-02a00c7be52b00368"]
      security_groups = [aws_security_group.c9-internet-archiver-dashboard-securitygroup.id]
      assign_public_ip = true
    }
}

# task definition for the website
resource "aws_ecs_task_definition" "c9-internet-archiver-website-taskdef" {
    family = "c9-internet-archiver-website-taskdef"
    network_mode = "awsvpc"
    requires_compatibilities = ["FARGATE"]
    container_definitions = jsonencode([
        {
            name: "c9-internet-archiver-website"
            image: "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c9-internet-archiver-website:latest"
            essential: true
            portMappings: [{
                containerPort = 5000
                hostPort = 5000
            }]
            environment: [
                { name: "DB_IP", value: var.DB_IP },
                { name: "DB_PORT", value: var.DB_PORT },
                { name: "DB_NAME", value: var.DB_NAME },
                { name: "DB_USERNAME", value: var.DB_USERNAME},
                { name: "DB_PASSWORD", value: var.DB_PASSWORD },
                { name: "AWS_ACCESS_KEY_ID", value: var.AWS_ACCESS_KEY_ID },
                { name: "AWS_SECRET_ACCESS_KEY", value: var.AWS_SECRET_ACCESS_KEY },
                { name: "S3_BUCKET", value: var.S3_BUCKET },
                { name: "URL_TABLE_NAME", value: var.URL_TABLE_NAME },
                { name: "SCRAPE_TABLE_NAME", value: var.SCRAPE_TABLE_NAME },
                { name: "OPENAI_API_KEY", value: var.OPENAI_API_KEY }
                
            ],
            "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": var.AWS_GROUP,
                "awslogs-region": var.AWS_REGION,
                "awslogs-stream-prefix": var.AWS_STREAM_PREFIX,
                "awslogs-create-group": "true"
            }
        }
    }
    ])
    execution_role_arn = data.aws_iam_role.execution-role.arn
    memory = 2048
    cpu = 1024
}

# security group to allow inbound traffic on port 5000 for the website
resource "aws_security_group" "c9-internet-archiver-website-securitygroup" {
  name        = "c9-internet-archiver-website-securitygroup"
  description = "Allow inbound traffic for port 5000, so users can see the website"
  vpc_id      = "vpc-04423dbb18410aece"

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# start ECS service for the dashboard
resource "aws_ecs_service" "c9-internet-archiver-website-service" {
    name = "c9-internet-archiver-website-service"
    cluster = data.aws_ecs_cluster.c9-cluster.id
    task_definition = aws_ecs_task_definition.c9-internet-archiver-website-taskdef.arn
    desired_count = 1
    launch_type = "FARGATE"
    network_configuration {
      subnets = ["subnet-0d0b16e76e68cf51b", "subnet-081c7c419697dec52", "subnet-02a00c7be52b00368"]
      security_groups = [aws_security_group.c9-internet-archiver-website-securitygroup.id]
      assign_public_ip = true
    }
}