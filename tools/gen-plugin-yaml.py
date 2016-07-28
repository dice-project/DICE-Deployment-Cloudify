#!/usr/bin/env python
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

from __future__ import print_function

import os
import sys
import yaml
import argparse

from string import Template


def get_version(root):
    init = {}
    with open(os.path.join(root, "dice_plugin", "__init__.py")) as f:
        exec(f.read(), init)
    return init["__version__"]


def get_repo(repo, version):
    return Template(repo).substitute(VERSION=version)



def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def merge(a, b):
    """
    Merge dicts a and b recursively
    """
    for k in b.keys():
        if isinstance(b[k], dict) and k in a and isinstance(a[k], dict):
            merge(a[k], b[k])
        else:
            a[k] = b[k]


def process_library(library_path, platform, chef_repo, plugin_repo):
    library = {}

    # Common types
    common = os.path.join(library_path, "common")
    yamls = (os.path.join(dir, f) for dir, _, files in os.walk(common)
                                  for f in files if f.endswith(".yaml"))
    for y in yamls:
        log("Processing '{}' ...".format(y))
        with open(y, "r") as input:
            merge(library, yaml.load(input))

    # Platform-dependent types
    platform = os.path.join(library_path, "{}.yaml".format(platform))
    log("Processing '{}' ...".format(platform))
    with open(platform, "r") as input:
        merge(library, yaml.load(input))

    log("Inserting Chef repo location ...")
    chef_component = library["node_types"]["dice.chef.SoftwareComponent"]
    chef_config = chef_component["properties"]["chef_config"]["default"]
    chef_config["chef_repo"] = chef_repo

    log("Inserting plugin repo location ...")
    dice_plugin = library["plugins"]["dice"]["source"] = plugin_repo

    return library


def save_output(library, output):
    output.write(yaml.dump(library, default_flow_style=False))


def main():
    root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    library = os.path.realpath(os.path.join(root, "library"))
    version = get_version(root)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-l", "--library", help="Library path", default=library
    )
    parser.add_argument(
        "-o", "--output", help="Ouptut file location", default=sys.stdout,
        type=argparse.FileType("w")
    )
    parser.add_argument(
        "-c", "--chef-repo", help="Path/URL to Chef repo tar.gz.",
        default=("https://github.com/dice-project/DICE-Chef-Repository/"
                 "archive/${VERSION}.tar.gz")
    )
    parser.add_argument(
        "-d", "--library-repo", help="Path/URL to DICE TOSCA repo zip.",
        default=("https://github.com/dice-project/DICE-Deployment-Cloudify/"
                 "archive/${VERSION}.zip")
    )
    parser.add_argument(
        "-v", "--version", help="Release version to generate", default=version
    )
    parser.add_argument(
        "platform", help="Platform for which library should be generated"
    )
    args = parser.parse_args()

    chef = get_repo(args.chef_repo, version)
    dice = get_repo(args.library_repo, version)

    library = process_library(args.library, args.platform, chef, dice)
    save_output(library, args.output)


if __name__ == "__main__":
    main()
