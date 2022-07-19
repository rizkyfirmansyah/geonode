GEOSERVER_EXT_DIR=/var/local/geoserver-exts
GEOSERVER_EXT_COMMUNITY_DOWNLOAD=${GEOSERVER_DOWNLOAD_URL}/${GEOSERVER_VERSION}/community-latest
GEOSERVER_EXT_COMMUNITY=cog,s3-geotiff,sec-oauth2-geonode,elasticsearch,wps-download,geopkg
GEOSERVER_EXT=geofence-server,control-flow,excel,libjpeg-turbo,wps,vectortiles,sldservice,importer,css,monitor,authkey,printing
GEOSERVER_EXT_DOWNLOAD=${GEOSERVER_DOWNLOAD_URL}/${GEOSERVER_VERSION}/ext-latest
CURL_OPTS=(-sfSL --retry 3)
DEBIAN_FRONTEND=noninteractive
GEOSERVER_BRANCH_VERSION=${GEOSERVER_VERSION::-2}

mkdir -p ${GEOSERVER_EXT_DIR}

for plugin in $GEOSERVER_EXT; do
  get_ext() {
    HTTP_CODE=$(curl ${CURL_OPTS[@]} -w "${http_code}" -o ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip ${GEOSERVER_EXT_DOWNLOAD}/geoserver-${GEOSERVER_BRANCH_VERSION}-SNAPSHOT-${plugin}-plugin.zip --silent)
  }
  if [ "$HTTP_CODE" = '200' ]; then
    unzip -q -o ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip -d ${GEOSERVER_WEB_LIB}
    rm ${GEOSERVER_EXT_DIR}/*
  fi
done

for plugin in $GEOSERVER_EXT_COMMUNITY; do
  get_ext_community() {
    HTTP_CODE=$(curl ${CURL_OPTS[@]} -w "${http_code}" -o ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip ${GEOSERVER_EXT_COMMUNITY_DOWNLOAD}/geoserver-${GEOSERVER_BRANCH_VERSION}-SNAPSHOT-${plugin}-plugin.zip --silent)
  }
  if [ "$HTTP_CODE" = '200' ]; then
    unzip -q -o ${GEOSERVER_EXT_DIR}/geoserver-${plugin}.zip -d ${GEOSERVER_WEB_LIB}
    rm ${GEOSERVER_EXT_DIR}/*
  fi
done