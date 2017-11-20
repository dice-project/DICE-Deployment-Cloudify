# Copyright (c) 2017 XLAB d.o.o.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import os

import yaml

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from dice_plugin import aws, fco, openstack, utils


PLATFORMS = dict(
    fco=fco,
    openstack=openstack,
    aws=aws,
)


def _get_platform(platform):
    if platform in PLATFORMS:
        return PLATFORMS[platform]
    raise NonRecoverableError("Missing platform: {}".format(platform))


def _load_plugin_configuration():
    path = "/etc/dice/dice.yaml"
    if "DICE_PLUGIN_CONFIG" in os.environ:
        path = os.environ["DICE_PLUGIN_CONFIG"]

    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except IOError:
        return {}


def _run_command(ctx, properties, stage):
    platform_name = properties["platform"]
    file_config = _load_plugin_configuration().get(platform_name, {})
    user_config = properties.get("platform_config", {}).get(platform_name, {})
    config = utils.merge_dicts(file_config, user_config)

    platform = _get_platform(platform_name)
    try:
        func = getattr(platform, stage)
    except AttributeError:
        msg = "Operation {} not implemented for {}"
        raise NonRecoverableError(msg.format(stage, platform))
    func(ctx, config["auth"], config["env"])


def _run_instance_command(ctx, stage):
    _run_command(ctx, ctx.node.properties, stage)


def _run_source_command(ctx, stage):
    _run_command(ctx, ctx.source.node.properties, stage)


@operation
def create_server(ctx):
    ctx.logger.info("Creating host instance {}".format(ctx.instance.id))
    _run_instance_command(ctx, "create_server")
    ctx.logger.info("Host instance {} created".format(ctx.instance.id))


@operation
def start_server(ctx):
    ctx.logger.info("Starting host instance {}".format(ctx.instance.id))
    _run_instance_command(ctx, "start_server")
    ctx.logger.info("Host instance {} started".format(ctx.instance.id))


@operation
def stop_server(ctx):
    ctx.logger.info("Stopping host instance {}".format(ctx.instance.id))
    _run_instance_command(ctx, "stop_server")
    ctx.logger.info("Host instance {} stopped".format(ctx.instance.id))


@operation
def delete_server(ctx):
    ctx.logger.info("Deleting host instance {}".format(ctx.instance.id))
    _run_instance_command(ctx, "delete_server")
    ctx.logger.info("Host instance {} deleted".format(ctx.instance.id))


@operation
def validate_server(ctx):
    pass


@operation
def create_firewall(ctx):
    ctx.logger.info("Creating firewall instance {}".format(ctx.instance.id))
    _run_instance_command(ctx, "create_firewall")
    ctx.logger.info("Firewall instance {} created".format(ctx.instance.id))


@operation
def delete_firewall(ctx):
    ctx.logger.info("Deleting firewall instance {}".format(ctx.instance.id))
    _run_instance_command(ctx, "delete_firewall")
    ctx.logger.info("Firewall instance {} deleted".format(ctx.instance.id))


@operation
def validate_firewall(ctx):
    pass


@operation
def apply_firewall(ctx):
    msg = "Securing host {} using firewall {}"
    ctx.logger.info(msg.format(ctx.source.instance.id, ctx.target.instance.id))
    _run_source_command(ctx, "apply_firewall")
    ctx.logger.info("Host instance {} secured".format(ctx.source.instance.id))


@operation
def detach_firewall(ctx):
    msg = "Removing host {} protection"
    ctx.logger.info(msg.format(ctx.source.instance.id))
    _run_source_command(ctx, "detach_firewall")
    ctx.logger.info("Host instance {} exposed".format(ctx.source.instance.id))


@operation
def create_virtual_ip(ctx):
    ctx.logger.info("Creating virtual ip instance {}".format(ctx.instance.id))
    _run_instance_command(ctx, "create_virtual_ip")
    ctx.logger.info("Virtual ip instance {} created".format(ctx.instance.id))


@operation
def delete_virtual_ip(ctx):
    ctx.logger.info("Deleting virtual ip instance {}".format(ctx.instance.id))
    _run_instance_command(ctx, "delete_virtual_ip")
    ctx.logger.info("Virtual ip instance {} deleted".format(ctx.instance.id))


@operation
def validate_virtual_ip(ctx):
    pass


@operation
def notify_virtual_ip(ctx):
    id = ctx.target.instance.id
    ctx.logger.info("Sending virtual ip notify to {}".format(id))
    _run_source_command(ctx, "notify_virtual_ip")
    ctx.logger.info("Virtual ip instance {} notified".format(id))


@operation
def connect_virtual_ip(ctx):
    msg = "Connecting host {} to virtual ip {}"
    ctx.logger.info(msg.format(ctx.source.instance.id, ctx.target.instance.id))
    _run_source_command(ctx, "connect_virtual_ip")
    ctx.logger.info("Host and virtual ip connected")


@operation
def disconnect_virtual_ip(ctx):
    msg = "Disconnecting host {} from virtual ip {}"
    ctx.logger.info(msg.format(ctx.source.instance.id, ctx.target.instance.id))
    _run_source_command(ctx, "disconnect_virtual_ip")
    ctx.logger.info("Host and virtual ip disconnected")


@operation
def create_image(ctx):
    ctx.logger.info("Creating image")
    _run_instance_command(ctx, "create_image")


@operation
def delete_image(ctx):
    ctx.logger.info("Deleting image {}".format(ctx.instance.id))
    _run_instance_command(ctx, "delete_image")
