source .env
export PGPASSWORD=$DB_PASSWORD
psql -h $DB_IP -U $DB_USERNAME -d $DB_NAME -p 5432 -f schema.sql
