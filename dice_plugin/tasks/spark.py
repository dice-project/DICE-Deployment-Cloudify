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

from dice_plugin import utils
from cloudify.decorators import operation


@operation
def submit(ctx, jar, name, klass, args):
    ctx.logger.info("Obtaining application jar '{}'".format(jar))
    local_jar = utils.obtain_resource(ctx, jar)
    ctx.logger.info("Application jar stored as '{}'".format(local_jar))

    ctx.logger.info("Submitting '{}' as '{}'".format(local_jar, name))
    base_cmd = ["spark-submit", "--deploy-mode", "client", "--class", klass,
                local_jar, name]
    ctx.logger.info("COMMAND: {}".format(base_cmd + args))
    proc, log = utils.call(base_cmd + args, run_in_background=True)
    ctx.logger.info("LOG FILE: {}".format(log))
