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

from __future__ import absolute_import

import string

from cloudify.decorators import operation

import docker


def _get_docker_client(host):
    return docker.DockerClient(base_url=host)


def _expand_command(command, rt_props):
    if command is None:
        return None

    formatter = string.Formatter()
    values = {}
    for item in formatter.parse(command):
        if item[1]:
            values[item[1]] = rt_props[item[1]]
    return formatter.format(command, **values)


@operation
def create(ctx, command, host, image, tag, ports):
    """
    Create new docker container from image.
    """
    props = ctx.node.properties
    rt_props = ctx.instance.runtime_properties

    ctx.logger.info("Creating new container from image {}.".format(image))
    client = _get_docker_client(host)

    kwargs = {}
    if props["registry_auth"] is not None:
        kwargs["auth_config"] = props["registry_auth"]

    client.images.pull(image, tag=tag, **kwargs)
    img = "{}:{}".format(image, tag)
    container = client.containers.create(
        img, detach=True, ports=ports,
        command=_expand_command(command, rt_props)
    )
    rt_props["id"] = container.id
    rt_props["name"] = container.name


def _get_ports(container):
    """
    {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "99"}]} -> {"80/tcp": "99"}
    """
    ports = container.attrs["NetworkSettings"]["Ports"]
    return {k: v[0]["HostPort"] for k, v in ports.items()}


@operation
def start(ctx, host, container_id):
    """
    Start selected docker container.
    """
    ctx.logger.info("Starting container {}.".format(container_id))
    client = _get_docker_client(host)
    container = client.containers.get(container_id)
    container.start()
    container.reload()
    ctx.instance.runtime_properties["port_mapping"] = _get_ports(container)


@operation
def stop(ctx, host, container_id):
    """
    Stop selected docker container.
    """
    if container_id is not None:
        ctx.logger.info("Stopping container {}.".format(container_id))
        _get_docker_client(host).containers.get(container_id).stop()


@operation
def delete(ctx, host, container_id):
    """
    Remove selected docker container.
    """
    if container_id is not None:
        ctx.logger.info("Removing container {}.".format(container_id))
        _get_docker_client(host).containers.get(container_id).remove()
