#!/bin/bash

# This script will collect all the zookeeper servers and store
# their IPs in the source's (i.e., the zookeeper node's)
# runtime parameters.

SOURCE_INSTANCE_ID=$(ctx source instance id)
TARGET_INSTANCE_ID=$(ctx target instance id)
TARGET_HOST_IP=$(ctx target instance host_ip)

ctx logger info "Source instance id: $SOURCE_INSTANCE_ID"
ctx logger info "Target instance id: $TARGET_INSTANCE_ID"
ctx logger info "Target host ip: $TARGET_HOST_IP"

ctx source instance runtime_properties "zookeeper_servers.$TARGET_INSTANCE_ID" "$TARGET_HOST_IP"
