# web_scraper
This folder is related to the script we use that re-scrapes all of URLs we have stored every couple of hours and uploads the new versions into the S3 bucket and RDS.

## Assumptions
In order for the web_scraper code to work, there are a few assumptions that need to be made:

- You have a database that contains the required tables, can be added by running the following command in the database directory:
`psql -h `DB_HOST`  -U `DB_USERNAME` -d `DB_NAME` -p `DB_PORT` -f schema.sql`
You will then be asked to enter a password and the tables required will be added.

- You have an S3 bucket where files can be uploaded freely.

Both of these things can be made automatically by using the terraform folder.

- You have entered a few links into the database to be tracked, using `app.py` found in the api folder

## Environment Variables
The code used environment variables. As a result, you will need to create a file called ``.env`. Within that file, you will need the following details:

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

## Files Explained
- `extract.py` is the file containing all of the functions used to extract the pages from the database and re-scrape them.
- `load.py` is the file containing all of the functions used to load the newly scraped pages back into the S3 bucket and RDS.
- `pipeline.py` is the file which ties the `extract.py` and `load.py` files together, a complete script completing the whole process.
- `requirements.txt` is the file containing all the modules needed to run the code.
- `Dockerfile` is the file which allows the script to be dockerised and run on AWS on an automatic trigger, requiring no human interference.

## How to run it (MANUALLY)
In order to run the terraform code, once you have the `.env` file setup, then the following commands can be used:
1. `python3 -m venv venv` : Creates a virtual environment.
2. `source venv/bin/activate` : Activates the virtual environment.
3. `pip3 install -r requirements.txt` : Downloads all of the modules needed to run the code.
4. `python3 pipeline.py` : Runs the entire pipeline and re-scrapes all of your links currently in the database, unless blocked.

And then finally, if you want to run it automatically every 3 hours every day:

1. Create an ECR repository.
2. Terraform the files (instructions found in terraform folder).
3. Follow the push commands given in the ECR repository using the Dockerfile.
4. Automatic web scraping should now occur.