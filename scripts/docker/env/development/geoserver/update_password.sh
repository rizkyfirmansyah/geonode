#!/bin/bash

# Reference
# https://github.com/kartoza/docker-geoserver/blob/master/scripts/update_passwords.sh

SETUP_LOCKFILE="${GEOSERVER_DATA_DIR}/.updatepassword.lock"

USERS_XML=${USERS_XML:-${GEOSERVER_DATA_DIR}/security/usergroup/default/users.xml}
CLASSPATH=${CLASS_PATH:-${GEOSERVER_WEB_LIB}}

make_hash(){
  NEW_PASSWORD=$1
  (echo "digest1:" && java -classpath $(find $CLASSPATH -regex ".*jasypt-[0-9]\.[0-9]\.[0-9].*jar") org.jasypt.intf.cli.JasyptStringDigestCLI digest.sh algorithm=SHA-256 saltSizeBytes=16 iterations=100000 input="$NEW_PASSWORD" verbose=0) | tr -d '\n'
}

PWD_HASH=$(make_hash $GEOSERVER_ADMIN_PASSWORD)

# users.xml setup
cp $USERS_XML $USERS_XML.orig

cat $USERS_XML.orig | sed -e "s/ name=\".*\" / name=\"${GEOSERVER_ADMIN_USER}\" /" | sed -e "s/ password=\".*\"/ password=\"${PWD_HASH//\//\\/}\"/" > $USERS_XML

if [ "${GEOSERVER_ADMIN_PASSWORD}" ]; then
  echo -e "[Entrypoint] Generated Geoserver Password: \e[1;31m $GEOSERVER_ADMIN_PASSWORD"
fi

# put lock file to make sure password is not reinitialized on restart
touch ${SETUP_LOCKFILE}