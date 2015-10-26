#!/bin/bash

CONFIG_FILE=/etc/zookeeper/conf/zoo.cfg
echo "server.0=$(ctx target instance runtime-properties ip):2888:3888" | sudo tee -a $CONFIG_FILE
ctx logger info "Updated the zookeeper's configuration"
