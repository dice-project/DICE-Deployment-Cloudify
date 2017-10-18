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

from dice_plugin import general


# This module contains some ugly hacks around the inflexibility of cloudify.
# It would be possible to refactor the core and avoid this monstrosity, but
# since we may need to migrate to aria soon-ish, we will do the cleanup at a
# later time.

@operation
def create(ctx):
    general.create_image(ctx)
    rtprops = ctx.instance.runtime_properties
    props = ctx.node.properties
    rtprops["_image"] = rtprops.copy()
    dict.__setitem__(props, "image", rtprops["openstack_id"])
    general.create_server(ctx)


@operation
def delete(ctx):
    general.delete_server(ctx)
    rtprops = ctx.instance.runtime_properties
    rtprops.update(rtprops["_image"])
    general.delete_image(ctx)
