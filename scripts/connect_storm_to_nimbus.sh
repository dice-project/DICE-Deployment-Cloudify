#!/bin/bash

SOURCE_INSTANCE_ID=$(ctx source instance id)
TARGET_INSTANCE_ID=$(ctx target instance id)
TARGET_HOST_IP=$(ctx target instance host_ip)

ctx logger info "Connecting storm $SOURCE_INSTANCE_ID to nimbus $TARGET_INSTANCE_ID"
ctx logger info "Target host ip: $TARGET_HOST_IP"

ctx source instance runtime_properties nimbus_server_address "$TARGET_HOST_IP"

ctx logger info "Done."
