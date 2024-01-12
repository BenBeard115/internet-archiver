# Database
This folder is related to the scripts used to create a database for the Internet Archiver Website.

## Assumptions
To create the database, a `.env` file is required with the variables specified below. Then the database can be created with `bash reset_schema.sh`.

## Environment Variables
The code used environment variables. As a result, you will need to create a file called `.env`. Within that file, you will need the following details:

- `DB_IP` : The IP address of your database, found on AWS.
- `DB_PORT` : The port that your database is using, normally 5432.
- `DB_NAME` : The host name or address of a database server.
- `DB_USERNAME` : The username that the database logs in by.
- `DB_PASSWORD` : The password required to log in.
- `AWS_ACCESS_KEY_ID` : The access key that can be found on AWS.
- `AWS_SECRET_ACCESS_KEY` : The secret access key that only you should know, on AWS.

## Files Explained
- `schema.sql`: An SQL script that sets up the database and all the tables within.
- `reset_schema.sh`: A bash script that runs the schema, creating the database.
- `login.sh`: A bash script that logs into the database for manual inspection.
