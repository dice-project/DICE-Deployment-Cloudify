#!/bin/bash

echo "10.10.43.121 finesce-chef-server.xlab.si finesce-chef-server" | sudo tee -a /etc/hosts
echo "127.0.1.1 $HOSTNAME" | sudo tee -a /etc/hosts

ctx logger info "Configured chef server host name"

for n in $(seq 255)
do
  echo "109.231.122.$n 109-231-122-$n" | sudo tee -a /etc/hosts
done

ctx logger info "Patched /etc/hosts file"

echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsrH2o/WY+DLTJ/gxzIIV4slSkk0b+qQTteIDYidjcSdl0sp5HaE3UVhJ0xRP3LSVK4+SKC6LW/42N6/XzXX1V+O0CmAEVXxfhu97ZMbK1C8+iyo4bNVzabgI5pzUIAsh8c8WWBMgrey5O9MJkzDv8heZaauB+C1uw6G/uF5fFrhvYGVPokb1YaFKsq0cqkPG6usINByxPmgDV2LIHXkPKMktodyGFXmvk+Z9wWqVEzyzaQbnarXXaTd73LupFJAJBQdwm08LCasDs/sunSrr9m4KxDv+sKN0ybxZFjPIOrK2fUzMF1t6u4WTsdZ107G6u/KieEuMlchGVbJ3UDMsnQ== matej@virtubuntutej" >> ~/.ssh/authorized_keys
