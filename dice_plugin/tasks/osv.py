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

from cloudify.decorators import operation

import yaml

from dice_plugin import general, utils


# This module contains some ugly hacks around the inflexibility of cloudify.
# It would be possible to refactor the core and avoid this monstrosity, but
# since we may need to migrate to aria soon-ish, we will do the cleanup at a
# later time.

def _inject_monitoring_vars(props, user_data):
    if not props["monitoring"]["enabled"]:
        return user_data

    data = {} if user_data == "" else yaml.safe_load(user_data)

    vars = utils.get_monitoring_vars(props["monitoring"])
    cmds = [dict(POST="/env/{}".format(name), val=value)
            for name, value in vars.items()]

    # Variables are added at the start of the run list. This ensures that all
    # commands that follow have access to their values.
    cmds.extend(data.get("run", []))
    data["run"] = cmds

    return yaml.safe_dump(data, default_flow_style=False)


@operation
def create(ctx, image, instance_type, user_data):
    props = ctx.node.properties
    if not props["use_existing"]:
        general.create_image(ctx, image)
        rtprops = ctx.instance.runtime_properties
        rtprops["_image"] = rtprops.copy()
        image = rtprops["openstack_id"]
    user_data = _inject_monitoring_vars(props, user_data)
    # disk_type is set to dummy because OSv does not support FCO and this
    # platform is the only one that would require meaningful value here.
    general.create_server(ctx, image=image, instance_type=instance_type,
                          disk_type="dummy", user_data=user_data)


@operation
def delete(ctx):
    general.delete_server(ctx)
    rtprops = ctx.instance.runtime_properties
    if "_image" in rtprops:
        rtprops.update(rtprops["_image"])
        general.delete_image(ctx)
