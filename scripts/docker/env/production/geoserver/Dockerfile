FROM tomcat:9-jre8
LABEL organization="WRI Indonesia"
LABEL maintainer="Rizky Firmansyah <rizky.firmansyah@wri.org>"

# Set GeoServer version and data directory
ARG DB_CMS_HOST
ARG DB_CMS_PORT
ARG DB_GIS_HOST
ARG DB_GIS_PORT
ARG GEOSERVER_VERSION
ARG GEOSERVER_DATA_DIR
ARG HIKARI=false
ARG JNDI=false
ARG TOMCAT_EXTRAS=false
ARG DEFAULT_GEOSERVER_DIR=true
ARG ENABLE_LIBJPEG=false
ARG GEONODE_DATABASE
ARG GEONODE_DATABASE_PASSWORD=${GEONODE_DATABASE_PASSWORD}
ARG GEONODE_GEODATABASE
ARG GEONODE_DATABASE_GF
ARG GEONODE_GEODATABASE_USER
ARG GEONODE_GEODATABASE_PASSWORD=${GEONODE_GEODATABASE_PASSWORD}
ARG GEONODE_GEODATABASE_SCHEMA
ARG GEONODE_MONITORING_DATABASE
ARG OAUTH2_CLIENT_ID
ARG OAUTH2_CLIENT_SECRET
ARG HTTP_HOST
ARG RABBITMQ_DEFAULT_USER
ARG RABBITMQ_DEFAULT_PASS=${RABBITMQ_DEFAULT_PASS}
ARG GEONODE_REST_SEC_DIR="${GEOSERVER_DATA_DIR}/security/role/geonode REST role service"
ARG GEOSERVER_GEOSOLUTION=true

ENV DB_GIS_HOST=${DB_GIS_HOST}
ENV DB_GIS_PORT=${DB_GIS_PORT}
ENV DB_CMS_HOST=${DB_CMS_HOST}
ENV DB_CMS_PORT=${DB_CMS_PORT}
ENV GEOSERVER_DATA_DIR=${GEOSERVER_DATA_DIR}
ENV GEONODE_DATABASE=${GEONODE_DATABASE}
ENV GEONODE_GEODATABASE=${GEONODE_GEODATABASE}
ENV GEONODE_DATABASE_GF=${GEONODE_DATABASE_GF}
ENV GEONODE_GEODATABASE_USER=${GEONODE_GEODATABASE_USER}
ENV GEONODE_GEODATABASE_SCHEMA=${GEONODE_GEODATABASE_SCHEMA}
ENV GEONODE_MONITORING_DATABASE=${GEONODE_MONITORING_DATABASE}
ENV GEOSERVER_VERSION=${GEOSERVER_VERSION}
ENV HTTP_HOST=${HTTP_HOST}
ENV OAUTH2_CLIENT_ID=${OAUTH2_CLIENT_ID}
ENV RABBITMQ_DEFAULT_USER=${RABBITMQ_DEFAULT_USER}

ENV GEOSERVER_INSTALL_DIR /usr/local/geoserver
ENV POSTGRESQL_JDBC postgresql-42
ENV HIKARICP_VERSION 4.0.3
ENV CATALINA_HOME /usr/local/tomcat
ENV GEOSERVER_WEB_LIB ${CATALINA_HOME}/webapps/geoserver/WEB-INF/lib
ENV GEOSERVER_DOWNLOAD_URL https://build.geoserver.org/geoserver
ENV GEOSOLUTION_DOWNLOAD_URL https://artifacts.geonode.org/geoserver
ENV MARLIN_JAR ${GEOSERVER_WEB_LIB}/marlin-0.9.3.jar
ENV GEOSERVER_EXT_COMMUNITY cog
ENV GEOSERVER_EXT geofence-server control-flow libjpeg-turbo wps gwc-s3 vectortiles sldservice importer css monitor authkey printing querylayer
ENV LD_LIBRARY_PATH /usr/lib/jni:/usr/local/lib:/usr/lib:/opt/libjpeg-turbo/lib64:/usr/local/tomcat/native-jni-lib:/usr/local/tomcat/lib:$LD_LIBRARY_PATH
ENV LIBJPEG_TURBO_VERSION 2.1.3

# produce errors if any then stop
RUN set -x \
  && apt-get update \
  && apt-get install -y curl unzip apt-utils debconf \
  && echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections \
  && apt-get install -y ttf-mscorefonts-installer fontconfig \
  && apt-get purge -y apt-utils \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*

## Optionally remove tomcat manager, docs and examples
RUN if [ "$TOMCAT_EXTRAS" = false ]; then \
  rm -rf ${CATALINA_HOME}/webapps/ROOT && \
  rm -rf ${CATALINA_HOME}/webapps/docs && \
  rm -rf ${CATALINA_HOME}/webapps/examples && \
  rm -rf ${CATALINA_HOME}/webapps/host-manager && \
  rm -rf ${CATALINA_HOME}/webapps/manager; \
  fi;

# Download and install GeoServer
SHELL ["/bin/bash", "-ceux"]
RUN if [ "$GEOSERVER_GEOSOLUTION" = true ]; then \
      mkdir -p ${GEOSERVER_INSTALL_DIR}; \
      cd ${GEOSERVER_INSTALL_DIR}; \
      wget --no-check-certificate --progress=bar:force:noscroll ${GEOSOLUTION_DOWNLOAD_URL}/${GEOSERVER_VERSION}/geoserver.war -O geoserver.war; \
      unzip -q geoserver.war -d ${CATALINA_HOME}/webapps/geoserver; \
      mkdir -p ${GEOSERVER_DATA_DIR}; \
      mv ${CATALINA_HOME}/webapps/geoserver/data/* ${GEOSERVER_DATA_DIR}; \
    fi;

SHELL ["/bin/bash", "-ceux"]
RUN if [ "$GEOSERVER_GEOSOLUTION" = false ]; then \
      mkdir -p ${GEOSERVER_INSTALL_DIR}; \
      cd ${GEOSERVER_INSTALL_DIR}; \
      wget --no-check-certificate --progress=bar:force:noscroll ${GEOSERVER_DOWNLOAD_URL}/${GEOSERVER_VERSION}/geoserver-${GEOSERVER_VERSION}-latest-war.zip -O geoserver.war.zip; \
      unzip -q geoserver.war.zip geoserver.war; \
      unzip -q geoserver.war -d ${CATALINA_HOME}/webapps/geoserver; \
      mkdir -p ${GEOSERVER_DATA_DIR}; \
      mv ${CATALINA_HOME}/webapps/geoserver/data/* ${GEOSERVER_DATA_DIR}; \
    fi;

# INSTALL GEOSERVER EXTENSION
# ref https://github.com/boonen/docker-geoserver/blob/master/stable/openjdk11/Dockerfile

SHELL ["/bin/bash", "-ceux"]
RUN if [ "$GEOSERVER_GEOSOLUTION" = false ]; then \
      export GEOSERVER_EXT_DOWNLOAD=${GEOSERVER_DOWNLOAD_URL}/${GEOSERVER_VERSION}/ext-latest; \
      export GEOSERVER_EXT_COMMUNITY_DOWNLOAD=${GEOSERVER_DOWNLOAD_URL}/${GEOSERVER_VERSION}/community-latest; \
      export GEOSERVER_EXT_DIR=/var/local/geoserver-exts; \
      export CURL_OPTS=(-sfSL --retry 3); \
      export DEBIAN_FRONTEND=noninteractive; \
      GEOSERVER_BRANCH_VERSION=${GEOSERVER_VERSION%.*}; \
      mkdir -p ${GEOSERVER_EXT_DIR}; \
      for plugin in $GEOSERVER_EXT; do \
        curl ${CURL_OPTS[@]} -o ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip ${GEOSERVER_EXT_DOWNLOAD}/geoserver-${GEOSERVER_BRANCH_VERSION}-SNAPSHOT-${plugin}-plugin.zip; \
        unzip -q -o ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip -d ${GEOSERVER_WEB_LIB}; \
        rm ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip; \
      done; \
      for plugin in $GEOSERVER_EXT_COMMUNITY; do \
        curl ${CURL_OPTS[@]} -o ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip ${GEOSERVER_EXT_COMMUNITY_DOWNLOAD}/geoserver-${GEOSERVER_BRANCH_VERSION}-SNAPSHOT-${plugin}-plugin.zip; \
        unzip -q -o ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip -d ${GEOSERVER_WEB_LIB}; \
        rm ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip; \
      done; \
    fi;

SHELL ["/bin/bash", "-ceux"]
RUN if [ "$ENABLE_LIBJPEG" = true ]; then \
    export CURL_OPTS=(-sfSL --retry 3); \
    curl ${CURL_OPTS[@]} -o libjpeg-turbo.deb https://downloads.sourceforge.net/project/libjpeg-turbo/${LIBJPEG_TURBO_VERSION}/libjpeg-turbo-official_${LIBJPEG_TURBO_VERSION}_amd64.deb; \
    dpkg -i libjpeg-turbo.deb; \
    ln -s /opt/libjpeg-turbo/lib64/libjpeg.so.62.3.0 /usr/lib/libjpeg.so.62; \
    rm libjpeg-turbo.deb; \
    fi;

SHELL ["/bin/bash", "-ceux"]
RUN if [ "$HIKARI" = true ]; then \
  # hikaricp plugin
  export CURL_OPTS=(-sfSL --retry 3) ; \
  curl ${CURL_OPTS[@]} -o ${CATALINA_HOME}/lib/HikariCP-${HIKARICP_VERSION}.jar https://search.maven.org/remotecontent?filepath=com/zaxxer/HikariCP/${HIKARICP_VERSION}/HikariCP-${HIKARICP_VERSION}.jar; \
  # enable postgis jndi in your tomcat configuration
  sed -i '\:</Context>:i \
  <Resource name="jdbc/geodb"\n\
  auth="Container"\n\
  type="javax.sql.DataSource"\n\
  factory="com.zaxxer.hikari.HikariJNDIFactory"\n\
  driverClassName="org.postgresql.Driver"\n\
  jdbcUrl="jdbc:postgresql://'${DB_GIS_HOST}':'${DB_GIS_PORT}'/'${GEONODE_GEODATABASE}'"\n\
  username="'${GEONODE_GEODATABASE_USER}'"\n\
  password="'${GEONODE_GEODATABASE_PASSWORD}'"\n\
  keepaliveTime="300000" minimumIdle="5" maximumPoolSize="25" connectionTimeout="300000" maxLifetime="1800000" />\n\
  ' ${CATALINA_HOME}/conf/context.xml ; \
  cd ${CATALINA_HOME}/lib ; \
  cp ${GEOSERVER_WEB_LIB}/{log4j,slf4j-api}-* ${CATALINA_HOME}/lib/ ; \
  # copy oauth2 spring security library
  cp ${GEOSERVER_WEB_LIB}/{gs-sec-oauth2,spring-security-oauth2}-* ${CATALINA_HOME}/lib/ ; \
  fi;

# set up PostGIS JNDI connection instead of default connection
# read more at https://doc-geonode.readthedocs.io/en/latest/006_adv_workshop/003_geonode_production/adv_gsconfig/db_pooling.html
SHELL ["/bin/bash", "-ceux"]
RUN if [ "$JNDI" = true ]; then \
  # enable postgis jndi in your tomcat configuration
  sed -i '\:</Context>:i \
  <Resource\n\
  name="jdbc/postgres" auth="Container" type="javax.sql.DataSource"\n\
  driverClassName="org.postgresql.Driver"\n\
  url="jdbc:postgresql://'${DB_GIS_HOST}':'${DB_GIS_PORT}'/'${GEONODE_GEODATABASE}'"\n\
  username="'${GEONODE_GEODATABASE_USER}'"\n\
  password="'${GEONODE_GEODATABASE_PASSWORD}'"\n\
  maxTotal="50"\n\
  maxIdle="10"\n\
  maxWaitMillis="10000"\n\
  minEvictableIdleTimeMillis="300000"\n\
  timeBetweenEvictionRunsMillis="300000"\n\
  validationQuery="SELECT 1"/>\n\
  ' ${CATALINA_HOME}/conf/context.xml ; \
  mv ${GEOSERVER_WEB_LIB}/${POSTGRESQL_JDBC}*.jar ${CATALINA_HOME}/lib/; \
  fi;

WORKDIR ${GEOSERVER_WEB_LIB}
# get postgis jdbc and remove default h2 hibernate spatial as well as other required jar
RUN wget --no-check-certificate https://repo1.maven.org/maven2/org/postgis/postgis-jdbc/1.3.3/postgis-jdbc-1.3.3.jar && \
  wget --no-check-certificate https://maven.geo-solutions.it/org/hibernatespatial/hibernate-spatial-postgis/1.1.3.2/hibernate-spatial-postgis-1.1.3.2.jar

RUN mkdir -p ${CATALINA_HOME}/tmp
# remove bcprov-jdk15on to prevent dependency hierarcy due to StackOverflowError
# ref here https://stackoverflow.com/questions/17584495/unable-to-complete-the-scan-for-annotations-for-web-application-app-due-to-a
RUN mv ${GEOSERVER_WEB_LIB}/bcprov-jdk15on-1.69.jar ${CATALINA_HOME}/tmp/

# copy the script and perform the run of scripts from entrypoint.sh
WORKDIR ${CATALINA_HOME}/tmp
COPY update_password.sh ${CATALINA_HOME}/tmp
COPY entrypoint.sh ${CATALINA_HOME}/tmp

### change default template to your site url and its database configuration
COPY ./templates/geofence/geofence-datasource-ovr.properties ${GEOSERVER_DATA_DIR}/geofence/geofence-datasource-ovr.properties
COPY ./templates/monitoring/db.properties ${GEOSERVER_DATA_DIR}/monitoring/db.properties
COPY ./templates/notifier/notifier.xml ${GEOSERVER_DATA_DIR}/notifier/notifier.xml
COPY ./templates/security/geonode-oauth2/config.xml ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml
COPY ./templates/security/role/config.xml ${GEONODE_REST_SEC_DIR}/config.xml
COPY ./templates/global.xml ${GEOSERVER_DATA_DIR}/global.xml

# change dynamic variable with sed
RUN sed -i "s/{GEONODE_DATABASE}/${GEONODE_DATABASE}/g" ${GEOSERVER_DATA_DIR}/geofence/geofence-datasource-ovr.properties
RUN sed -i "s/{GEONODE_DATABASE_PASSWORD}/${GEONODE_DATABASE_PASSWORD}/g" ${GEOSERVER_DATA_DIR}/geofence/geofence-datasource-ovr.properties
RUN sed -i "s/{GEONODE_DATABASE_PASSWORD}/${GEONODE_DATABASE_PASSWORD}/g" ${GEOSERVER_DATA_DIR}/geofence/geofence-datasource-ovr.properties
RUN sed -i "s/{GEONODE_DATABASE_GF}/${GEONODE_DATABASE_GF}/g" ${GEOSERVER_DATA_DIR}/geofence/geofence-datasource-ovr.properties
RUN sed -i "s/{DB_CMS_HOST}/${DB_CMS_HOST}/g" ${GEOSERVER_DATA_DIR}/geofence/geofence-datasource-ovr.properties
RUN sed -i "s/{DB_CMS_PORT}/${DB_CMS_PORT}/g" ${GEOSERVER_DATA_DIR}/geofence/geofence-datasource-ovr.properties
RUN sed -i "s/{GEONODE_GEODATABASE_SCHEMA}/${GEONODE_GEODATABASE_SCHEMA}/g" ${GEOSERVER_DATA_DIR}/geofence/geofence-datasource-ovr.properties

RUN sed -i "s/{GEONODE_DATABASE}/${GEONODE_DATABASE}/g" ${GEOSERVER_DATA_DIR}/monitoring/db.properties
RUN sed -i "s/{GEONODE_DATABASE_PASSWORD}/${GEONODE_DATABASE_PASSWORD}/g" ${GEOSERVER_DATA_DIR}/monitoring/db.properties
RUN sed -i "s/{GEONODE_MONITORING_DATABASE}/${GEONODE_MONITORING_DATABASE}/g" ${GEOSERVER_DATA_DIR}/monitoring/db.properties

RUN sed -i "s/{RABBITMQ_DEFAULT_USER}/${RABBITMQ_DEFAULT_USER}/g" ${GEOSERVER_DATA_DIR}/notifier/notifier.xml
RUN sed -i "s/{RABBITMQ_DEFAULT_PASS}/${RABBITMQ_DEFAULT_PASS}/g" ${GEOSERVER_DATA_DIR}/notifier/notifier.xml

RUN sed -i "s/{OAUTH2_CLIENT_ID}/${OAUTH2_CLIENT_ID}/g" ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml
RUN sed -i "s/{OAUTH2_CLIENT_SECRET}/${OAUTH2_CLIENT_SECRET}/g" ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml
RUN sed -i "s/{HTTP_HOST}/https:\/\/${HTTP_HOST}/g" ${GEOSERVER_DATA_DIR}/security/filter/geonode-oauth2/config.xml

RUN sed -i "s/{HTTP_HOST}/https:\/\/${HTTP_HOST}/g" "${GEONODE_REST_SEC_DIR}/config.xml"
RUN sed -i "s/{HTTP_HOST}/https:\/\/${HTTP_HOST}/g" "${GEOSERVER_DATA_DIR}/global.xml"

RUN chmod +x ${CATALINA_HOME}/tmp/update_password.sh
RUN chmod +x ${CATALINA_HOME}/tmp/entrypoint.sh

# create default java options, if you have GEOSERVER_JAVA_OPTS this config parameters will override by your GEOSERVER_JAVA_OPTS
ENV JAVA_OPTS="-Djava.awt.headless=true -Xms6G -Xmx10G -XX:+UnlockDiagnosticVMOptions -XX:+LogVMOutput -XX:LogFile=/var/log/jvm.log -XX:PerfDataSamplingInterval=500 -XX:SoftRefLRUPolicyMSPerMB=36000 -XX:-UseGCOverheadLimit -XX:+UseConcMarkSweepGC -XX:ParallelGCThreads=4 -Dfile.encoding=UTF8 -Djavax.servlet.request.encoding=UTF-8 -Djavax.servlet.response.encoding=UTF-8 -Duser.timezone=GMT+7 -Dorg.geotools.shapefile.datetime=false -DGEOSERVER_CSRF_DISABLED=true -DPRINT_BASE_URL=https://${HTTP_HOST}/geoserver/pdf -DALLOW_ENV_PARAMETRIZATION=true -Xbootclasspath/a:/usr/local/tomcat/webapps/geoserver/WEB-INF/lib/marlin-0.9.3-Unsafe.jar -Dsun.java2d.renderer=org.marlin.pisces.MarlinRenderingEngine"

ENTRYPOINT ["/usr/local/tomcat/tmp/entrypoint.sh"]
