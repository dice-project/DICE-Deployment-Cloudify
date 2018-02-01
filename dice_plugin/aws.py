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

from functools import wraps

import boto3


def _get_session(auth):
    return boto3.session.Session(**auth)


def _get_client(auth):
    return _get_session(auth).client("ec2")


def _get_resource(auth):
    return _get_session(auth).resource("ec2")


def _get_resource_name(ctx):
    return "{}-{}".format(ctx.deployment.id, ctx.instance.id)


def _get_id(ctx):
    return ctx.instance.runtime_properties.get("aws_id")


def _set_id(ctx, id):
    ctx.instance.runtime_properties["aws_id"] = id


def _remove_id(ctx):
    ctx.instance.runtime_properties.pop("aws_id", None)


def _transform_rule(rule):
    if "port" in rule:
        from_port, to_port = int(rule["port"]), int(rule["port"])
    else:
        from_port, to_port = int(rule["from_port"]), int(rule["to_port"])
    return dict(
        IpProtocol=rule["protocol"],
        FromPort=from_port,
        ToPort=to_port,
        CidrIp=rule["ip_prefix"],
    )


def _gather_all_security_group_ids(instance):
    return [rel.target.instance.runtime_properties["aws_id"]
            for rel in instance.relationships
            if rel.type == "dice.relationships.ProtectedBy"]


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

    # Ugly: we need to gather all attached security groups before we create
    # new server, because AWS platform does not support adding security groups,
    # only replacing the whole list, which is prone to race conditions.
    groups = _gather_all_security_group_ids(ctx.instance)
    groups.append(env["default_security_group_id"])

    resource = _get_resource(auth)
    server = resource.create_instances(
        ImageId=ctx.node.properties["image"],
        InstanceType=ctx.node.properties["instance_type"],
        SubnetId=env["subnet_id"],
        SecurityGroupIds=groups,
        KeyName=env["key_name"],
        MinCount=1, MaxCount=1
    )[0]
    _set_id(ctx, server.id)
    server.create_tags(Tags=[dict(Key="Name", Value=name)])

    server.wait_until_exists()
    server.load()
    ctx.instance.runtime_properties["ip"] = server.private_ip_address


def start_server(ctx, auth, _):
    name = _get_resource_name(ctx)
    ctx.logger.info("Starting server {}".format(name))

    resource = _get_resource(auth)
    server = resource.Instance(_get_id(ctx))
    server.wait_until_running()


@skip_if_missing
def stop_server(ctx, id, auth, _):
    ctx.logger.info("Stopping server {}".format(id))
    resource = _get_resource(auth)
    server = resource.Instance(id)
    server.stop()
    server.wait_until_stopped()


@skip_if_missing
def delete_server(ctx, id, auth, _):
    ctx.logger.info("Deleting server {}".format(id))
    resource = _get_resource(auth)
    server = resource.Instance(id)
    server.terminate()
    server.wait_until_terminated()
    _remove_id(ctx)


def create_firewall(ctx, auth, env):
    name = _get_resource_name(ctx)
    ctx.logger.info("Creating security group {}".format(name))

    resource = _get_resource(auth)
    group = resource.create_security_group(VpcId=env["vpc_id"],
                                           GroupName=name,
                                           Description=name)
    _set_id(ctx, group.id)

    ctx.logger.info("Adding security group rules")
    for rule in ctx.node.properties["rules"]:
        group.authorize_ingress(**_transform_rule(rule))


@skip_if_missing
def delete_firewall(ctx, id, auth, env):
    ctx.logger.info("Deleting security group {}".format(id))
    _get_resource(auth).SecurityGroup(id).delete()
    _remove_id(ctx)


def apply_firewall(ctx, auth, env):
    pass


def detach_firewall(ctx, auth, env):
    pass


def create_virtual_ip(ctx, auth, env):
    ctx.logger.info("Creating floating ip")
    client = _get_client(auth)
    ip = client.allocate_address(Domain="vpc")
    _set_id(ctx, ip["AllocationId"])
    ctx.instance.runtime_properties["address"] = ip["PublicIp"]


@skip_if_missing
def delete_virtual_ip(ctx, id, auth, env):
    ctx.logger.info("Deleting floating ip {}".format(id))
    _get_resource(auth).VpcAddress(id).release()
    _remove_id(ctx)


def notify_virtual_ip(ctx, auth, env):
    pass


def connect_virtual_ip(ctx, auth, env):
    ctx.logger.info("Adding floating ip to server")
    target = ctx.target.instance
    source = ctx.source.instance

    resource = _get_resource(auth)
    ip = resource.VpcAddress(target.runtime_properties["aws_id"])
    assoc = ip.associate(InstanceId=source.runtime_properties["aws_id"])
    target.runtime_properties["aws_assoc_id"] = assoc["AssociationId"]


def disconnect_virtual_ip(ctx, auth, env):
    ctx.logger.info("Removing floating ip from server")
    target = ctx.target.instance

    assoc_id = target.runtime_properties.pop("aws_assoc_id", None)
    if assoc_id is None:
        return

    client = _get_client(auth)
    client.disassociate_address(AssociationId=assoc_id)
