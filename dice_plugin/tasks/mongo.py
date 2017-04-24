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

import json
import random
import re
import string
import tempfile

from cloudify.decorators import operation

from dice_plugin import utils


def _prep_replica_script(members, type, name):
    is_cfg = type == "config"
    members = [dict(_id=i, host="{}:27017".format(m))
               for i, m in enumerate(members)]
    payload = dict(_id=name, configsvr=is_cfg, members=members)
    return "rs.initiate({});".format(json.dumps(payload))


@operation
def establish_replica(ctx):
    s_rt_props = ctx.source.instance.runtime_properties
    t_rt_props = ctx.target.instance.runtime_properties
    t_props = ctx.target.node.properties

    if t_rt_props["fqdn"] != s_rt_props["members"][0]:
        return  # Only first member instantiates replica, all others do nothing

    ctx.logger.info("Creating replica {}".format(ctx.target.node.id))
    script = _prep_replica_script(s_rt_props["members"], t_props["type"],
                                  ctx.target.node.id)
    ctx.logger.debug("Replica script: {}".format(script))

    with tempfile.NamedTemporaryFile(suffix=".js") as f:
        f.write(script)
        f.flush()
        cmd = ["mongo", "--host", t_rt_props["fqdn"], f.name]
        ctx.logger.debug("Calling {}".format(cmd))
        proc, log = utils.call(cmd, run_in_background=False)
        proc.wait()
        ctx.logger.debug("Return value: {}".format(proc.returncode))

    with open(log, "r") as f:
        ctx.logger.debug("Mongo output:")
        ctx.logger.debug(f.read())

    if proc.returncode != 0:
        # We rety here because mongod is a bit slow when it comes to starting
        ctx.operation.retry("Mongo failed to create replica")

    s_rt_props["replica_name"] = ctx.target.node.id


def _prep_shard_script(host, name):
    return 'sh.addShard("{}/{}:27017")'.format(name, host)


@operation
def add_shard(ctx):
    s_rt_props = ctx.source.instance.runtime_properties
    t_rt_props = ctx.target.instance.runtime_properties

    ctx.logger.info("Adding shard {}".format(t_rt_props["replica_name"]))
    script = _prep_shard_script(t_rt_props["members"][0],
                                t_rt_props["replica_name"])
    ctx.logger.debug("Shard script: {}".format(script))

    cmd = ["mongo", "--host", s_rt_props["fqdn"], "--eval", script]
    ctx.logger.debug("Calling {}".format(cmd))
    proc, log = utils.call(cmd, run_in_background=False)
    proc.wait()
    with open(log, "r") as f:
        ctx.logger.debug("Mongo output:")
        ctx.logger.debug(f.read())

    if proc.returncode != 0:
        # We rety here because mongos is a bit slow when it comes to starting
        ctx.operation.retry("Mongo failed to add shard")


@operation
def get_replica_data(ctx):
    msg = "Gathering data from replica {}"
    ctx.logger.info(msg.format(ctx.target.instance.id))

    name = ctx.target.instance.runtime_properties["replica_name"]
    ctx.source.instance.runtime_properties["replica_name"] = name

    members = ctx.target.instance.runtime_properties["members"]
    ctx.source.instance.runtime_properties["members"] = members


def _prepare_add_user_script(username, password, dbs):
    roles = [dict(role="readWrite", db=db["db_name"]) for db in dbs]
    user = dict(user=username, pwd=password, roles=roles)
    return 'db.getSiblingDB("admin").createUser({})'.format(json.dumps(user))


@operation
def create_user(ctx):
    props = ctx.node.properties
    attrs = ctx.instance.runtime_properties

    ctx.logger.info("Creating user {}".format(props["username"]))

    host = next(rel for rel in ctx.instance.relationships
                if rel.type == "dice.relationships.ContainedIn").target
    admin_user = host.instance.runtime_properties["admin_user"]
    admin_pass = host.instance.runtime_properties["admin_pass"]

    chars = string.letters + string.digits
    user_pass = ''.join(random.choice(chars) for _ in range(30))
    script = _prepare_add_user_script(props["username"], user_pass,
                                      attrs["databases"])

    cmd = ["mongo", "-u", admin_user, "-p", admin_pass,
           "--authenticationDatabase", "admin", "--eval", script]
    proc, log = utils.call(cmd, run_in_background=False)
    proc.wait()
    with open(log, "r") as f:
        ctx.logger.debug("Mongo output:")
        ctx.logger.debug(f.read())

    if proc.returncode != 0:
        # We rety here because mongo is a bit slow when it comes to starting
        ctx.operation.retry("Mongo failed to add user")

    attrs["password"] = user_pass


@operation
def monitor_db(ctx):
    if not ctx.node.properties["monitoring"]["enabled"]:
        ctx.logger.info("Monitoring is disabled. Skiping registration.")
        return

    config_file = "/etc/collectd/collectd.conf.d/mongo.conf"
    name = ctx.node.properties["name"]
    ctx.logger.info("Adding {} to monitored database list".format(name))

    with open(config_file) as c:
        config = c.read()

    if re.search(r"Database[^\n]*{}".format(name), config) is not None:
        return  # Database already monitored

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(re.sub(r"(Database.*)\n", r'\1 "{}"\n'.format(name), config))

    utils.call(["sudo", "cp", f.name, config_file], False)[0].wait()
    utils.call(["sudo", "systemctl", "restart", "collectd"], False)[0].wait()
