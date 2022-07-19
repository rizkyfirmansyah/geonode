#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -h 127.0.0.1 <<-EOSQL
    CREATE DATABASE geofence OWNER sdi;
    GRANT ALL PRIVILEGES ON DATABASE geofence TO sdi;
    GRANT ALL PRIVILEGES ON DATABASE monitoring TO sdi;
    \c geofence;
    CREATE EXTENSION postgis;
EOSQL