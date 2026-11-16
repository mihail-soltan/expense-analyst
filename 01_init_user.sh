#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v app_user="$APP_DB_USER" \
  -v app_pass="$APP_DB_PASSWORD" <<-EOSQL
    CREATE USER :"app_user" WITH PASSWORD :'app_pass';
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO :"app_user";
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"app_user";
EOSQL