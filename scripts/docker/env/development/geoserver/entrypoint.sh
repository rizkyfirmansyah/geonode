#!/bin/bash
set -e

source /root/.bashrc

if [ ! -z "${GEOSERVER_JAVA_OPTS}" ]
then

    echo "GEOSERVER_JAVA_OPTS is filled so I replace the value of '$JAVA_OPTS' with '$GEOSERVER_JAVA_OPTS' \n"
    JAVA_OPTS=${GEOSERVER_JAVA_OPTS}

fi

if [ "${CATALINA_HOME}/tmp/update_password.sh" ]; then
    ${CATALINA_HOME}/tmp/update_password.sh
fi

# install additional extension
# source ${CATALINA_HOME}/tmp/extension.sh
# start tomcat
exec env JAVA_OPTS="${JAVA_OPTS}" catalina.sh run
