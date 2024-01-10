# Dashboard
This folder is related to the script we use that creates a dashboard displaying statistics pertaining to the Internet Archiver Website.

## Assumptions
In order for the dashboard code to work, there are a few assumptions that need to be made:

- Run `bash reset_database.sh` in the database folder to create the database and tables
- You have an S3 bucket where files can be uploaded freely.

Both of these things can be made automatically by using the terraform folder.

- You have entered a few links into the database to be tracked, using `app.py` found in the api folder

## Environment Variables
The code used environment variables. As a result, you will need to create a file called `.env`. Within that file, you will need the following details:

- `S3_BUCKET` : The name of the bucket made either by terraform, or manually.
- `DB_IP` : The IP address of your database, found on AWS.
- `DB_PORT` : The port that your database is using, normally 5432.
- `DB_NAME` : The host name or address of a database server.
- `DB_USERNAME` : The username that the database logs in by.
- `DB_PASSWORD` : The password required to log in.
- `AWS_ACCESS_KEY_ID` : The access key that can be found on AWS.
- `AWS_SECRET_ACCESS_KEY` : The secret access key that only you should know, on AWS.

## Files Explained
- `extract.py` is the file containing all of the functions used to extract the data from the database.
- `download_screenshot.py` is the file containing all of the functions used to extract the screenshots from the s3 bucket.
- `dashboard_functions.py` is the file containing all of the functions used to create the database.
- `dashboard.py` is the file which creates the database when run.
- `requirements.txt` is the file containing all the modules needed to run the code.
- `Dockerfile` is the file which allows the script to be dockerised and run on AWS as a service.
- `.streamlit` is a folder containing the config for the dashboard.
- `archive_image.png` is the image used as an icon for the dashboard google tab.

## How to run it (MANUALLY)
In order to run the terraform code, once you have the `.env` file setup, then the following commands can be used:
1. `python3 -m venv venv` : Creates a virtual environment.
2. `source venv/bin/activate` : Activates the virtual environment.
3. `pip3 install -r requirements.txt` : Downloads all of the modules needed to run the code.
4. `streamlit run dashboard.py` : Runs the entire dashboard.

And then finally, if you want to run it as an aws service:

1. Create an ECR repository.
2. Terraform the files (instructions found in terraform folder).
3. Follow the push commands given in the ECR repository using the Dockerfile.