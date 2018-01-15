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

from __future__ import absolute_import

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from dice_plugin import utils


@operation
def set_attributes(ctx, **attrs):
    ctx.logger.info("Updating instance attributes.")
    instance = _get_instance(ctx)
    instance.runtime_properties.update(attrs)


@operation
def copy_ip_from_target(ctx, property):
    msg = "Copying ip address of '{}' into '{}' runtime property"
    ctx.logger.info(msg.format(ctx.target.instance.id, property))
    address = ctx.target.instance.host_ip
    ctx.source.instance.runtime_properties[property] = address


@operation
def copy_fqdn_from_target(ctx, property):
    msg = "Copying FQDN of '{}' into '{}' runtime property"
    ctx.logger.info(msg.format(ctx.target.instance.id, property))
    ctx.source.instance.runtime_properties[property] = utils.get_fqdn()


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


@operation
def download_resources(ctx, resource_pairs):
    for destination_key, source in resource_pairs:
        if source is None or source == "":
            ctx.logger.info("Skipping key '{}'".format(destination_key))
            location = None
        else:
            ctx.logger.info("Downloading '{}'".format(source))
            location = utils.obtain_resource(ctx, source)
        ctx.instance.runtime_properties[destination_key] = location


def _collect_item(source, item_mappings):
    return {v: source[k] for k, v in item_mappings.items()}


def _collect_data(instance, rel_type, selector):
    invalid_selectors = set(selector.keys()) - {"attributes", "properties"}
    if len(invalid_selectors) > 0:
        raise NonRecoverableError(
            "Unknown selector(s): {}".format(invalid_selectors)
        )

    data = []
    rels = (rel for rel in instance.relationships if rel.type == rel_type)
    for rel in rels:
        item = _collect_item(rel.target.node.properties,
                             selector.get("properties", {}))
        item.update(_collect_item(rel.target.instance.runtime_properties,
                                  selector.get("attributes", {})))
        data.append(item)

    return data


def _get_instance(ctx):
    return ctx.instance if ctx.type == "node-instance" else ctx.source.instance


@operation
def collect_data_for_rel(ctx, rel_type, dest_attr, selector, container="dict"):
    msg = "Collecting data from nodes, related by {}, into {}"
    ctx.logger.info(msg.format(rel_type, dest_attr))

    instance = _get_instance(ctx)
    data = _collect_data(instance, rel_type, selector)

    if container == "list":
        if len(data[0]) != 1:
            msg = "Cannot select more than one piece of data from targets"
            raise NonRecoverableError(msg)
        ctx.logger.info("Converting data to list")
        data = [i.popitem()[1] for i in data]

    rt_props = instance.runtime_properties
    rt_props[dest_attr] = data
