# Terraform
This folder is related to creating most of the AWS resources that we need through the use of Terraform.

## Assumptions
In order for the Terraform code to work, there are a few assumptions that need to be made:

- You have three ECRs already made contained with images for the dashboard, website and auto web-scraper, which can be dockerised using the Docker files within the other folders. The commands required can be found in each repository.

## Environment Variables
The code used environment variables. As a result, you will need to create a file called `terraform.tfvars`. Within that file, you will need the following details:

- `S3_BUCKET` : The name of the bucket made either by terraform, or manually.
- `DB_IP` : The IP address of your database, found on AWS.
- `DB_PORT` : The port that your database is using, normally 5432.
- `DB_NAME` : The host name or address of a database server.
- `DB_USERNAME` : The username that the database logs in by.
- `DB_PASSWORD` : The password required to log in.
- `AWS_ACCESS_KEY_ID` : The access key that can be found on AWS.
- `AWS_SECRET_ACCESS_KEY` : The secret access key that only you should know, on AWS.
- `URL_TABLE_NAME` : The table name used for urls, if you used the schema would be `url`.
- `SCRAPE_TABLE_NAME` : The table name used for page information, if you used the schema would be `page_scrape`.
These bottom three options are used for logging the task definitions, if you are not interested then feel free to delete the logging options section on the terraform for the auto-scraper task definition. Your preferred method can be found on AWS in the logging options when creating a task definition.
- `AWS_GROUP`
- `AWS_REGION`
- `AWS_STREAM_PREFIX`

## Files Explained
- `main.tf` is the central configuration file. It describes the infrastructure resources you want to manage.
- `variables.tf` is what is used to load the environment variables into the main file.

## How to run it
In order to run the terraform code, once you have the `terraform.tfvars` file setup, then the following commands can be used:
1. `terraform init` : Initialises the file.
2. `terraform plan` : Create an execution plan.
3. `terraform apply` : Allows you to execute your planned changes from the previous step.

And then finally, if you decide that if you want to stop the whole system, you can use:

4. `terraform destroy` : Destroys all resources defined previously.