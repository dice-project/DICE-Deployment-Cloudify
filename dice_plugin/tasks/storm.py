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


@operation
def submit_topology(ctx, jar, name, klass):
    if "topology_id" in ctx.source.instance.runtime_properties:
        ctx.logger.info("Topology '{}' already submitted".format(name))
        return

    ctx.logger.info("Obtaining topology jar '{}'".format(jar))
    local_jar = utils.obtain_resource(ctx, jar)

    ctx.logger.info("Submitting '{}' as '{}'".format(local_jar, name))
    try:
        subprocess.check_call(["storm", "jar", local_jar, klass, name])
    except subprocess.CalledProcessError:
        raise NonRecoverableError("Topology submission failed")

    ctx.logger.info("Retrieving topology id for '{}'".format(name))
    nimbus_ip = ctx.target.instance.host_ip
    url = "http://{}:8080/api/v1/topology/summary".format(nimbus_ip)
    topology_id = _get_topology_id(url, name)
    if topology_id is None:
        raise NonRecoverableError("Topology id cannot be found")
    ctx.source.instance.runtime_properties["topology_id"] = topology_id
