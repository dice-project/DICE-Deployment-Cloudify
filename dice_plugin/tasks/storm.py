# -*- coding: utf-8 -*-

# Copyright (C) 2016 XLAB d.o.o.
#
# This file is part of dice-plugin.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, * WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. * See the
# License for the specific language governing permissions and * limitations
# under the License.
#
# Author:
#     Tadej Borovšak <tadej.borovsak@xlab.si>

import json
import requests
import subprocess

from dice_plugin import utils
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError


def _get_topology_id(url, name):
    topologies = requests.get(url).json()["topologies"]
    for top in topologies:
        if top["name"] == name:
            return top["id"]
    return None


def _prepare_config_args(config):
    # Convert {"a.b": 123, "e": "f"} -> ["-c", "a.b=123", "-c", "e=f"]
    config_args = []
    for conf_item in config.items():
        config_args.append("-c")
        config_args.append("{}={}".format(*conf_item))
    return config_args


@operation
def submit_topology(ctx, jar, name, klass, args):
    ctx.logger.info("Obtaining topology jar '{}'".format(jar))
    local_jar = utils.obtain_resource(ctx, jar)
    ctx.logger.info("Topology jar stored as '{}'".format(local_jar))

    ctx.logger.info("Preparing topology configuration")
    cfg = ctx.node.properties["configuration"].copy()
    cfg.update(ctx.instance.runtime_properties.get("configuration", {}))
    config_args = _prepare_config_args(cfg)

    cmd = ["storm"] + config_args + ["jar", local_jar, klass, name] + args
    ctx.logger.info("Executing '{}'".format(" ".join(cmd)))
    subprocess.call(cmd)

    ctx.logger.info("Retrieving topology id for '{}'".format(name))
    nimbus_ip = ctx.instance.host_ip
    url = "http://{}:8080/api/v1/topology/summary".format(nimbus_ip)
    topology_id = _get_topology_id(url, name)
    ctx.logger.info("Topology id for '{}' is '{}'".format(name, topology_id))

    if topology_id is None:
        msg = "Topology '{}' failed to start properly".format(name)
        raise NonRecoverableError(msg)
    ctx.instance.runtime_properties["topology_id"] = topology_id


@operation
def register_topology(ctx, topology_id, monitoring):
    if not monitoring["enabled"]:
        ctx.logger.info("Monitoring is disabled. Skiping registration.")
        return

    dmon_tmpl = "http://{dmon_address}/dmon/v1/overlord/core/ls"
    dmon_logstash_endpoint = dmon_tmpl.format(**monitoring)
    nimbus_ip = ctx.instance.host_ip

    msg = "Registering topology {} to dmon {}."
    ctx.logger.info(msg.format(topology_id, dmon_logstash_endpoint))

    ctx.logger.info("Checking if topology is actually running.")
    topology_url = "http://{}:8080/api/v1/topology/{}".format(nimbus_ip,
                                                              topology_id)
    rst_json = requests.get(topology_url).json()
    if (len(rst_json["bolts"]) == 0) and (len(rst_json["spouts"]) == 0):
        ctx.operation.retry("Topology is not running yet")

    ctx.logger.info("Getting the current configuration from dmon.")
    r = requests.get(dmon_logstash_endpoint)
    if r.status_code != 200:
        msg = "Failed to obtain the configuration: {}\n{}"
        raise NonRecoverableError(msg.format(r.status_code, r.text))

    logstash_cfg = json.loads(r.text)["LS Instances"][0]
    topology_cfg = {
        "ESClusterName": logstash_cfg["ESClusterName"],
        "HostFQDN": logstash_cfg["HostFQDN"],
        "LSCoreStormTopology": topology_id,
        "LSCoreStormPort": 8080,
        "LSCoreStormEndpoint": nimbus_ip,
    }

    ctx.logger.info("Registering with: {}".format(json.dumps(topology_cfg)))
    r = requests.put("{}/config".format(dmon_logstash_endpoint),
                     json=topology_cfg)
    ctx.logger.info("Response: {}".format(r.text))

    if r.status_code != 201:
        msg = "Failed to update logstash configuration: {}\n{}"
        raise NonRecoverableError(msg.format(r.status_code, r.text))

    ctx.logger.info("Requesting logstash restart.")
    r = requests.post(dmon_logstash_endpoint)
    ctx.logger.info("Response: {0}".format(r.text))


@operation
def kill_topology(ctx, name):
    ctx.logger.info("Killing topology '{}'".format(name))
    subprocess.call(["storm", "kill", name])
