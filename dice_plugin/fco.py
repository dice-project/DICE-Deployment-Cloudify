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

import itertools
import json

from cloudify.exceptions import NonRecoverableError

from fcoclient import Client, resources


def _get_client(config):
    return Client(**config)


def _get_disk_skeleton(ctx, env):
    disk_type = ctx.node.properties["disk_type"]
    disk_name = "{}-{}-disk".format(ctx.deployment.id, ctx.instance.id)
    return resources.disk.Disk(disk_type, disk_name, 0, env["vdc_uuid"])


def _get_nic_skeleton(ctx, env):
    nic_name = "{}-{}-nic".format(ctx.deployment.id, ctx.instance.id)
    return resources.nic.Nic(env["network_uuid"], nic_name)


def _get_server_skeleton(ctx, env, disk, nic):
    server_type = ctx.node.properties["instance_type"]
    server_name = "{}-{}-server".format(ctx.deployment.id, ctx.instance.id)
    server_image = ctx.node.properties["image"]
    return resources.server.Server(server_type, server_name, env["vdc_uuid"],
                                   disks=[disk], nics=[nic],
                                   imageUUID=server_image)


def _get_firewall_skeleton(name, rules):
    return resources.firewalltemplate.FirewallTemplate(
        name, "IPV4", defaultInAction="REJECT", defaultOutAction="ALLOW",
        firewallInRuleList=_transform_rules(rules)
    )


def _get_server_address(server):
    for interface in server["nics"]:
        for address in interface["ipAddresses"]:
            if address["type"] == "IPV4":
                return address["ipAddress"]
    raise NonRecoverableError(
        "Server {} has no IPv4 address.".format(server.uuid)
    )


def _get_rt_prop(ctx, name):
    return ctx.instance.runtime_properties.get(name)


def _set_rt_prop(ctx, name, value):
    ctx.instance.runtime_properties[name] = value


def _del_rt_prop(ctx, name):
    ctx.instance.runtime_properties.pop(name, None)


def _gather_all_firewall_rules(instance):
    rules = []
    for rel in instance.relationships:
        node = rel.target.node
        if "dice.firewall_rules.Raw" in node.type_hierarchy:
            rules.extend(node.properties["rules"])
    return rules


def _inject_ssh_rules(template):
    template["firewallInRuleList"].extend([
        {
            "action": "ALLOW",
            "connState": "ALL",
            "direction": "IN",
            "icmpParam": "ECHO_REPLY_IPv4",
            "ipAddress": "0.0.0.0",
            "ipCIDRMask": 0,
            "localPort": 22,
            "name": "ssh-access",
            "protocol": "TCP",
            "remotePort": 0,
        }, {
            "action": "ALLOW",
            "connState": "EXISTING",
            "direction": "IN",
            "icmpParam": "ECHO_REPLY_IPv4",
            "ipAddress": "",
            "ipCIDRMask": 0,
            "localPort": 0,
            "name": "handshake",
            "protocol": "ANY",
            "remotePort": 0,
        }
    ])


def _transform_rules(rules):
    nested_transforms = (_transform_rule(r) for r in rules)
    return list(itertools.chain.from_iterable(nested_transforms))


def _transform_rule(rule):
    address, mask = rule["ip_prefix"].split("/")
    mask = int(mask)
    if "port" in rule:
        from_port, to_port = rule["port"], rule["port"]
    else:
        from_port = rule["from_port"]
        to_port = rule["to_port"]
    protocol = rule["protocol"].upper()

    return ({
        "action": "ALLOW",
        "connState": "ALL",
        "direction": "IN",
        "icmpParam": "ECHO_REPLY_IPv4",
        "ipAddress": address,
        "ipCIDRMask": mask,
        "localPort": port,
        "name": "rule-{}-{}".format(port, protocol),
        "protocol": protocol,
        "remotePort": 0,
    } for port in range(from_port, to_port + 1))


def create_server(ctx, auth, env):
    ctx.logger.info("Creating FCO instance")

    disk = _get_disk_skeleton(ctx, env)
    nic = _get_nic_skeleton(ctx, env)
    server = _get_server_skeleton(ctx, env, disk, nic)
    ctx.logger.debug("Server skeleton: {}".format(json.dumps(server)))

    client = _get_client(auth)
    job = client.server.create(server, [env["agent_key_uuid"]])
    job = client.job.wait(job.uuid)
    _set_rt_prop(ctx, "server_uuid", job.monitored_item_uuid)

    ctx.logger.debug("Job status: {}".format(json.dumps(job)))
    if job.status.marks_failure:
        raise NonRecoverableError("Failed to create server")

    server = client.server.get(uuid=job.monitored_item_uuid)
    server_address = _get_server_address(server)
    _set_rt_prop(ctx, "ip", server_address)
    ctx.logger.debug("Server: {}".format(json.dumps(server)))

    # Ugly: we need to merge all attached firewall rules into single firewall
    # template, because FCO platform does not support attaching more than one
    # firewall template to instance.
    rules = _gather_all_firewall_rules(ctx.instance)
    fw_name = "{}-{}-firewall".format(ctx.deployment.id, ctx.instance.id)
    firewall_skeleton = _get_firewall_skeleton(fw_name, rules)
    _inject_ssh_rules(firewall_skeleton)
    ctx.logger.debug("Firewall: {}".format(json.dumps(firewall_skeleton)))

    job = client.firewalltemplate.create(firewall_skeleton)
    job = client.job.wait(job.uuid)
    _set_rt_prop(ctx, "firewall_template_uuid", job.monitored_item_uuid)
    if job.status.marks_failure:
        raise NonRecoverableError("Failed to create firewall")

    job = client.firewalltemplate.apply(job.monitored_item_uuid,
                                        server_address)
    job = client.job.wait(job.uuid)
    ctx.logger.debug("Job status: {}".format(json.dumps(job)))
    if job.status.marks_failure:
        raise NonRecoverableError("Failed to apply firewall")


def start_server(ctx, auth, _):
    server_uuid = _get_rt_prop(ctx, "server_uuid")
    ctx.logger.info("Starting FCO instance {}".format(server_uuid))

    client = _get_client(auth)
    job = client.server.start(server_uuid)
    job = client.job.wait(job.uuid)
    ctx.logger.debug("Job status: {}".format(json.dumps(job)))
    if job.status.marks_failure:
        raise NonRecoverableError("Failed to start server")


def stop_server(ctx, auth, _):
    server_uuid = _get_rt_prop(ctx, "server_uuid")
    if server_uuid is None:
        return

    ctx.logger.info("Stopping FCO instance {}".format(server_uuid))

    client = _get_client(auth)
    job = client.server.stop(server_uuid)
    job = client.job.wait(job.uuid)
    ctx.logger.debug("Job status: {}".format(json.dumps(job)))
    if job.status.marks_failure:
        raise NonRecoverableError("Failed to stop server")


def delete_server(ctx, auth, _):
    client = _get_client(auth)

    # We delete server first to remove firewall temlate instantiation
    server_uuid = _get_rt_prop(ctx, "server_uuid")
    if server_uuid is not None:
        ctx.logger.info("Deleting FCO instance {}".format(server_uuid))
        job = client.server.delete(server_uuid, cascade=True)
        job = client.job.wait(job.uuid)
        ctx.logger.debug("Job status: {}".format(json.dumps(job)))
        if job.status.marks_failure:
            raise NonRecoverableError("Failed to delete server")
        _del_rt_prop(ctx, "server_uuid")

    firewall_uuid = _get_rt_prop(ctx, "firewall_template_uuid")
    if firewall_uuid is not None:
        ctx.logger.info("Deleting FCO firewall {}".format(firewall_uuid))
        job = client.firewalltemplate.delete(firewall_uuid)
        job = client.job.wait(job.uuid)
        ctx.logger.debug("Job status: {}".format(json.dumps(job)))
        if job.status.marks_failure:
            raise NonRecoverableError("Failed to delete server")
        _del_rt_prop(ctx, "firewall_template_uuid")


def create_firewall(ctx, auth, env):
    pass


def delete_firewall(ctx, auth, env):
    pass


def apply_firewall(ctx, auth, env):
    pass


def detach_firewall(ctx, auth, env):
    pass


def create_virtual_ip(ctx, auth, env):
    pass


def delete_virtual_ip(ctx, auth, env):
    pass


def notify_virtual_ip(ctx, auth, env):
    ctx.logger.info("Copying host address to virtual IP")
    address = ctx.source.instance.runtime_properties["ip"]
    ctx.target.instance.runtime_properties["address"] = address


def connect_virtual_ip(ctx, auth, env):
    pass


def disconnect_virtual_ip(ctx, auth, env):
    pass
