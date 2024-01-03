# Internet Archiver
## Setup and Installation
For some folders there will be a `requirements.txt` file. Once in the folder, you can run the following command:
- `pip3 install -r requirements.txt`

You will need to create a `.env` in every folder which contains:
-DB_NAME
-DB_IP
-DB_PORT
-DB_USERNAME
-DB_PASSWORD
-AWS_ACCESS_KEY_ID
-AWS_SECRET_ACCESS_KEY
-S3_BUCKET

## Files
### Api Folder
-`app.py`: A python script containing the main application, which makes the internet archiver website.
-`download_from_s3.py`: A python script which downloads css and html files from an s3 bucket.
-`upload_to_s3.py`: A python script which uploads css and html files to an s3 bucket.
-`extract_from_database.py`: A python script which extracts url data from a database.
-`upload_to_database.py`: A python script which uploads url data from a database.
-`requirements.txt`: A text file containing the required python libraries to run the website.

### Database Folder
-`schema.sql`: An SQL script that creates all the tables in the database.
-`reset_schema.sh`: A bash script that runs `schema.sql` to produce the tables.
-`login.sh`: A bash script that logs into the database for debugging purposes.

### Terraform Folder


### WebScraper Folder