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

import setuptools
import dice_plugin

setuptools.setup(
    name="dice-plugin",

    author="Tadej Borovšak",
    author_email="tadej.borovsak@xlab.si",
    description="DICE TOSCA library",
    license="LICENSE",

    version=dice_plugin.__version__,

    packages=setuptools.find_packages(exclude=["*.tests"]),
    package_data={
        "dice_plugin.tasks.data": ["index.html"],
    },
    zip_safe=False,
    install_requires=[
        "cloudify-plugins-common>=3.3.1",
        "requests",
        "pyyaml",
        "openstacksdk",
        "fcoclient",
        "boto3",
    ]
)
