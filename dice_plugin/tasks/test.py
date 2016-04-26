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


from cloudify import ctx
from cloudify.decorators import operation

import os
import signal
import shutil
import subprocess
from string import Template

from pkg_resources import resource_string


@operation
def configure(**kwargs):
    # Create toplevel folder
    server_root = "/tmp/python-simple-http-server"
    ctx.logger.info("Creating root folder '{}' ...".format(server_root))
    shutil.rmtree(server_root, True)
    os.makedirs(server_root)

    # Prepare index.html
    ctx.logger.info("Replacing template placeholders ...")
    index_content = resource_string(__name__, "data/index.html")
    template = Template(index_content)
    result = template.substitute(
        TITLE=ctx.node.properties["title"],
        DESCRIPTION=ctx.node.properties["description"]
    )
    with open("{}/index.html".format(server_root), "w") as output:
        output.write(result)

    # Save some properties for start and stop operations
    ctx.instance.runtime_properties["server_root"] = server_root


@operation
def start(**kwargs):
    port = ctx.node.properties["port"]
    command = "python -m SimpleHTTPServer {}".format(port)
    server_root = ctx.instance.runtime_properties["server_root"]

    ctx.logger.info("Starting simple HTTP server ...")
    with open(os.devnull, "r+b") as null:
        pid = subprocess.Popen(command.split(" "), stdout=null,
                               stderr=null, stdin=null, cwd=server_root).pid
    ctx.instance.runtime_properties["pid"] = pid


@operation
def stop(**kwargs):
    ctx.logger.info("Stopping simple HTTP server ...")
    os.kill(ctx.instance.runtime_properties["pid"], signal.SIGTERM)


@operation
def delete(**kwargs):
    ctx.logger.info("Removing server installation ...")
    shutil.rmtree(ctx.instance.runtime_properties["server_root"], True)
