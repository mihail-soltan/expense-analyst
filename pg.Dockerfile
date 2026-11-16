# syntax=docker/dockerfile:1
FROM postgres:17

COPY 01_init_user.sh /docker-entrypoint-initdb.d/01_init_user.sh
COPY init_pg_db.sql /docker-entrypoint-initdb.d/02_init_pg_db.sql

RUN chmod +x /docker-entrypoint-initdb.d/01_init_user.sh