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


@operation
def copy_runtime_prop(ctx, property):
    msg = "Copying runtime property '{}' from '{}' to '{}'"
    ctx.logger.info(msg.format(
        property, ctx.target.instance.id, ctx.source.instance.id
    ))
    prop = ctx.target.instance.runtime_properties[property]
    ctx.source.instance.runtime_properties[property] = prop


@operation
def copy_ip_from_target(ctx, property):
    msg = "Copying ip address of '{}' into '{}' runtime property"
    ctx.logger.info(msg.format(ctx.target.instance.id, property))
    address = ctx.target.instance.host_ip
    ctx.source.instance.runtime_properties[property] = address


@operation
def copy_ip_from_source(ctx, property):
    msg = "Copying ip address of '{}' into '{}' runtime property"
    ctx.logger.info(msg.format(ctx.source.instance.id, property))
    address = ctx.source.instance.host_ip
    ctx.target.instance.runtime_properties[property] = address


@operation
def update_configuration(ctx, configuration):
    ctx.logger.info("Updating configuration for '{}'".format(ctx.instance.id))
    ctx.instance.runtime_properties["configuration"] = configuration
