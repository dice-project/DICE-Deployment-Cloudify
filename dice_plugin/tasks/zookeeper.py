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

from cloudify.decorators import operation


QUORUM_MEMBER_PREFIX = "zoo_"
QUORUM_CONFIG_KEY = "zookeeper_quorum"


@operation
def gather_config(ctx):
    id = ctx.target.instance.id
    ip = ctx.target.instance.host_ip
    ctx.logger.info("Gathering IP address from {} ({})".format(id, ip))
    key = "{}{}".format(QUORUM_MEMBER_PREFIX, id)
    ctx.source.instance.runtime_properties[key] = ip


@operation
def merge_config(ctx):
    ctx.logger.info("Merging gathered data into complete configuration")
    props = ctx.instance.runtime_properties
    cfg = [v for k, v in props.items() if k.startswith(QUORUM_MEMBER_PREFIX)]
    ctx.instance.runtime_properties[QUORUM_CONFIG_KEY] = cfg


@operation
def retrieve_config(ctx):
    ctx.logger.info("Retrieving quorum configuration")
    cfg = ctx.target.instance.runtime_properties[QUORUM_CONFIG_KEY]
    ctx.source.instance.runtime_properties[QUORUM_CONFIG_KEY] = cfg
