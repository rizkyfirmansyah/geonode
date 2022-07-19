#!/bin/bash

# This script needs to be executed just once
if [ -f /$0.completed ] ; then
  echo "$0 `date` /$0.completed found, skipping run"
  exit 0
fi

# Execute RabbitMQ config commands here
( sleep 10 && \
rabbitmq-plugins enable rabbitmq_management && \
rabbitmqctl add_user ${RABBITMQ_DEFAULT_USER} ${RABBITMQ_DEFAULT_PASS} 2 > /dev/null && \
rabbitmqctl delete_user guest && \
rabbitmqctl set_user_tags ${RABBITMQ_DEFAULT_USER} administrator && \
rabbitmqctl add_vhost /localhost && \
rabbitmqctl set_permissions -p / ${RABBITMQ_DEFAULT_USER} ".*" ".*" ".*" && \
rabbitmqctl set_permissions -p /localhost ${RABBITMQ_DEFAULT_USER} ".*" ".*" ".*" && \
echo "*** User '$RABBITMQ_DEFAULT_USER' with password '$RABBITMQ_DEFAULT_PASS' completed. ***" && \
echo "*** Log in the WebUI at port 15672 (example: http://localhost:15672; or set up your reverse proxy using nginx) ***") & \

# $@ is used to pass arguments to the rabbitmq-server command.
# For example if you use it like this: docker run -d rabbitmq arg1 arg2,
# it will be as you run in the container rabbitmq-server arg1 arg2
rabbitmq-server
