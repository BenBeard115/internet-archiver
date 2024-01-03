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
    type = number
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