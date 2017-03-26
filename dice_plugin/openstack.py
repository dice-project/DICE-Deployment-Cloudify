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

# from cloudify.exceptions import NonRecoverableError

from __future__ import absolute_import

from functools import wraps

from openstack import connection, profile


def _get_client(auth):
    prof = profile.Profile()
    for k, v in auth["profile"].items():
        setter = "set_" + k
        getattr(prof, setter)(prof.ALL, v)
    return connection.Connection(profile=prof, **auth["connection"])


def _get_resource_name(ctx):
    return "{}-{}".format(ctx.deployment.id, ctx.instance.id)


def _get_id(ctx):
    return ctx.instance.runtime_properties.get("openstack_id")


def _set_id(ctx, id):
    ctx.instance.runtime_properties["openstack_id"] = id


def _remove_id(ctx):
    ctx.instance.runtime_properties.pop("openstack_id", None)


def _transform_rule(rule):
    if "port" in rule:
        from_port, to_port = rule["port"], rule["port"]
    else:
        from_port, to_port = rule["from_port"], rule["to_port"]
    return dict(
        direction="ingress",
        ethertype="IPv4",
        port_range_min=from_port,
        port_range_max=to_port,
        protocol=rule["protocol"],
        remote_ip_prefix=rule["ip_prefix"],
    )


def _get_server_address(server):
    return server.addresses.values()[0][0]["addr"]


def skip_if_missing(f):
    @wraps(f)
    def wrapper(ctx, auth, env):
        id = _get_id(ctx)
        if id is not None:
            f(ctx, id, auth, env)

    return wrapper


def create_server(ctx, auth, env):
    name = _get_resource_name(ctx)
    ctx.logger.info("Creating server {}".format(name))

    client = _get_client(auth)
    server = client.compute.create_server(
        name=name,
        image_id=ctx.node.properties["image"],
        flavor_id=ctx.node.properties["instance_type"],
        networks=[
            {"uuid": env["internal_network_id"]}
        ],
        security_groups=[dict(name=env["default_security_group_name"])],
        key_name=env["key_name"]
    )
    _set_id(ctx, server.id)

    server = client.compute.wait_for_server(server)
    ctx.instance.runtime_properties["ip"] = _get_server_address(server)
    ctx.logger.debug(server)


def start_server(ctx, auth, _):
    pass


@skip_if_missing
def stop_server(ctx, id, auth, _):
    ctx.logger.info("Stopping server {}".format(id))
    client = _get_client(auth)
    server = client.compute.get_server(id)
    client.compute.stop_server(server)
    client.compute.wait_for_server(server, status="SHUTOFF")


@skip_if_missing
def delete_server(ctx, id, auth, _):
    ctx.logger.info("Deleting server {}".format(id))
    client = _get_client(auth)
    client.compute.delete_server(id)
    _remove_id(ctx)


def create_firewall(ctx, auth, env):
    name = _get_resource_name(ctx)
    ctx.logger.info("Creating security group {}".format(name))

    client = _get_client(auth)
    sec_group = client.network.create_security_group(name=name)
    _set_id(ctx, sec_group.id)
    ctx.logger.debug(sec_group)

    ctx.logger.info("Adding security group rules")
    for rule in ctx.node.properties["rules"]:
        client.network.create_security_group_rule(
            security_group_id=sec_group.id, **_transform_rule(rule)
        )


@skip_if_missing
def delete_firewall(ctx, id, auth, env):
    ctx.logger.info("Deleting security group {}".format(id))
    client = _get_client(auth)
    client.network.delete_security_group(id)
    _remove_id(ctx)


def apply_firewall(ctx, auth, env):
    ctx.logger.info("Adding security group to server")
    client = _get_client(auth)
    client.compute.add_security_group_to_server(
        ctx.source.instance.runtime_properties["openstack_id"],
        ctx.target.instance.runtime_properties["openstack_id"]
    )


def detach_firewall(ctx, auth, env):
    ctx.logger.info("Removing security group from server")
    client = _get_client(auth)
    client.compute.remove_security_group_from_server(
        ctx.source.instance.runtime_properties["openstack_id"],
        ctx.target.instance.runtime_properties["openstack_id"]
    )


def create_virtual_ip(ctx, auth, env):
    ctx.logger.info("Creating floating ip")
    client = _get_client(auth)
    ip = client.network.create_ip(
        floating_network_id=env["external_network_id"]
    )
    _set_id(ctx, ip.id)
    ctx.instance.runtime_properties["address"] = ip.floating_ip_address
    ctx.logger.debug(ip)


@skip_if_missing
def delete_virtual_ip(ctx, id, auth, env):
    ctx.logger.info("Deleting floating ip {}".format(id))
    client = _get_client(auth)
    client.network.delete_ip(id)
    _remove_id(ctx)


def notify_virtual_ip(ctx, auth, env):
    pass


def connect_virtual_ip(ctx, auth, env):
    ctx.logger.info("Adding floating ip to server")
    client = _get_client(auth)
    client.compute.add_floating_ip_to_server(
        ctx.source.instance.runtime_properties["openstack_id"],
        ctx.target.instance.runtime_properties["address"]
    )


def disconnect_virtual_ip(ctx, auth, env):
    ctx.logger.info("Removing floating ip from server")
    client = _get_client(auth)
    client.compute.remove_floating_ip_from_server(
        ctx.source.instance.runtime_properties["openstack_id"],
        ctx.target.instance.runtime_properties["address"]
    )
