FROM python:3.8.9-buster
LABEL GeoNode development team

RUN mkdir -p /usr/src/geonode

# Enable postgresql-client-14
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list
RUN echo "deb http://deb.debian.org/debian/ stable main contrib non-free" | tee /etc/apt/sources.list.d/debian.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# This section is borrowed from the official Django image but adds GDAL and others
RUN apt-get update && apt-get install -y \
    libpq-dev python-dev libxml2-dev \
    libxml2 libxslt1-dev zlib1g-dev libjpeg-dev \
    libmemcached-dev libldap2-dev libsasl2-dev libffi-dev

RUN apt-get update && apt-get install -y \
    gcc zip gettext geoip-bin cron \
    sqlite3 spatialite-bin libsqlite3-mod-spatialite \
    python3-gdal python3-psycopg2 python3-ldap \
    python3-pip python3-pil python3-lxml python3-pylibmc \
    python3-dev libgdal-dev \
    uwsgi uwsgi-plugin-python3 \
    firefox-esr \
    --no-install-recommends

# add bower and grunt command
COPY . /usr/src/geonode/
WORKDIR /usr/src/geonode

COPY monitoring-cron /etc/cron.d/monitoring-cron
RUN chmod 0644 /etc/cron.d/monitoring-cron
RUN crontab /etc/cron.d/monitoring-cron
RUN touch /var/log/cron.log
RUN service cron start

RUN chmod +x /usr/src/geonode/tasks.py \
    && chmod +x /usr/src/geonode/entrypoint.sh

COPY celery.sh /usr/bin/celery-commands
RUN chmod +x /usr/bin/celery-commands

COPY celery-cmd /usr/bin/celery-cmd
RUN chmod +x /usr/bin/celery-cmd

# Preparing dependencies
RUN apt-get update && apt-get install -y devscripts build-essential debhelper pkg-kde-tools sharutils

# Install pip packages
RUN pip install pip --upgrade
RUN pip install --upgrade --no-cache-dir  --src /usr/src -r requirements.txt \
    && pip install pygdal==$(gdal-config --version).* \
    flower==0.9.4

RUN pip install --upgrade  -e .

# Activate "memcached"
RUN apt install memcached
RUN pip install pylibmc \
    && pip install sherlock

# Install "geonode-contribs" apps
RUN cd /usr/src; git clone https://github.com/GeoNode/geonode-contribs.git -b master
# Install logstash and centralized dashboard dependencies
RUN cd /usr/src/geonode-contribs/geonode-logstash; pip install --upgrade  -e . \
    cd /usr/src/geonode-contribs/ldap; pip install --upgrade  -e .

# Cleanup apt update lists
RUN rm -rf /var/lib/apt/lists/*

COPY package/geotools /mnt/volumes/statics/geoip

# Export ports
EXPOSE 8000

# We provide no command or entrypoint as this image can be used to serve the django project or run celery tasks
# ENTRYPOINT service cron restart && service memcached restart && /usr/src/geonode/entrypoint.sh
