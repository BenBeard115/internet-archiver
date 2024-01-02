# Terraform
This folder is related to creating most of the AWS resources that we need through the use of Terraform.

## Assumptions
In order for the Terraform code to work, there are a few assumptions that need to be made:
- 

## Environment Variables
The code used environment variables. As a result, you will need to create a file called `terraform.tfvars`. Within that file, you will need the following details:

- `DB_HOST` : The host name or address of a database server.\

## Files Explained
- `main.tf` is the central configuration file. It describes the infrastructure resources you want to manage.
- `variables.tf` is what is used to load the environment variables into the main file.

## How to run it
In order to run the terraform code, once you have the `terraform.tfvars` file setup, then the following commands can be used:
1. `terraform init` : Initialises the whole thing.
2. `terraform plan` : Create an execution plan.
3. `terraform apply` : Allows you to execute your planned changes from the previous step.

And then finally, if you decide that if you want to stop the whole system, you can use:

4. `terraform destroy` : Destroys all resources defined previously.