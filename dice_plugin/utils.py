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

import os
import copy
import shutil
import socket
import tempfile
import subprocess
import collections

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import requests


def parse_resource(path):
    url = urlparse(path)
    return (url.scheme == ""), url.path


def obtain_resource(ctx, resource, dir=None, keep_name=False):
    is_local, path = parse_resource(resource)
    if is_local:
        ctx.logger.info("Getting blueprint resource {}".format(path))
        file = ctx.download_resource(path)
    else:
        ctx.logger.info("Downloading resource from {}".format(resource))
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # TODO: Handle redirects here
            tmp.write(requests.get(resource, stream=True).raw.read())
        file = tmp.name

    # Move file if required
    name = os.path.basename(path) if keep_name else os.path.basename(file)
    dir = os.path.dirname(file) if dir is None else dir
    destination = os.path.join(dir, name)
    shutil.move(file, destination)

    ctx.logger.info("Resource saved to {}".format(destination))
    return destination


def call(cmd, run_in_background):
    cmd = [str(c) for c in cmd]
    if run_in_background:
        cmd.insert(0, "nohup")

    # TODO: Currently, we simply throw log data away. This should change once
    # we have proper job submission in place.
    handle, name = tempfile.mkstemp(suffix=".log")
    proc = subprocess.Popen(cmd, stdin=open(os.devnull, "r"),
                            stdout=handle, stderr=subprocess.STDOUT)
    return proc, name


def get_fqdn():
    return socket.getfqdn()


def merge_dicts(base, update):
    result = copy.deepcopy(base)
    for k, v in update.items():
        if isinstance(v, collections.Mapping):
            result[k] = merge_dicts(base.get(k, {}), v)
        else:
            result[k] = update[k]
    return result


def get_monitoring_vars(monitoring):
    """
    Extracts environment variables that applications can use to register with
    DMon from monitoring configuration.
    """
    return dict(
        DMON_HOST=monitoring["dmon_address"].split(":")[0],
        DMON_PORT=monitoring["dmon_address"].split(":")[1],
        GRAPHITE_PORT=monitoring["logstash_graphite_address"].split(":")[1],
        COLLECTD_PORT=monitoring["logstash_udp_address"].split(":")[1],
    )
