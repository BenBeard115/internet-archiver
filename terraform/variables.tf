variable "VPC_ID" {
    type = string
    default = "vpc-04423dbb18410aece"
}

variable "DB_USERNAME" {
    type = string
}

variable "DB_PASSWORD" {
    type = string
}

variable "DB_IP" {
    type = string
}

variable "S3_BUCKET" {
    type = string
}

variable "DB_PORT" {
    type = string
}

variable "DB_NAME" {
    type = string
}

variable "AWS_ACCESS_KEY_ID" {
    type = string
}

variable "AWS_SECRET_ACCESS_KEY" {
    type = string
}

variable "URL_TABLE_NAME" {
    type = string
}

variable "SCRAPE_TABLE_NAME" {
    type = string
}

variable "AWS_GROUP" {
    type = string
}

variable "AWS_REGION" {
    type = string
}

variable "AWS_STREAM_PREFIX" {
    type = string
}

variable "OPENAI_API_KEY" {
    type = string
}