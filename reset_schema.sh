source .env
psql --port=$DB_PORT --username=$DB_USERNAME --dbname=$DB_NAME -f schema.sql