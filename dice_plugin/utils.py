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

import urlparse
import requests
import tempfile


def parse_resource(path):
    url = urlparse.urlparse(path)
    return (url.scheme == ""), url.path


def obtain_resource(ctx, resource):
    is_local, path = parse_resource(resource)
    if is_local:
        ctx.logger.info("Getting blueprint resource {}".format(path))
        return ctx.download_resource(path)
    else:
        ctx.logger.info("Downloading resource from {}".format(resource))
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(requests.get(resource, stream=True).raw.read())
        tmp.close()
        return tmp.name
