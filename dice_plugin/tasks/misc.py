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

import os
import subprocess

from dice_plugin import utils
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError


@operation
def run_script(ctx, script, arguments, language):
    supported_langs = {"bash"}

    if language not in supported_langs:
        msg = "Unknown language: {}. Available languages: {}."
        raise NonRecoverableError(
            msg.format(language, ", ".join(supported_langs))
        )

    ctx.logger.info("Getting '{}' script".format(script))
    local_script = utils.obtain_resource(ctx, script)
    cmd = map(str, [language, local_script] + arguments)

    ctx.logger.info("Running command: {}".format(" ".join(cmd)))
    proc = subprocess.Popen(cmd, stdin=open(os.devnull, "r"),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(proc.stdout.readline, ""):
        ctx.logger.info(line.strip())
    proc.wait()

    if proc.returncode != 0:
        msg = "Script terminated with non-zero ({}) status."
        raise NonRecoverableError(msg.format(proc.returncode))

    ctx.instance.runtime_properties["ip"] = ctx.instance.host_ip
    ctx.instance.runtime_properties["fqdn"] = utils.get_fqdn()
