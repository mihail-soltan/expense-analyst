# syntax=docker/dockerfile:1
FROM postgres:17
COPY init_pg_db.sql /docker-entrypoint-initdb.d/