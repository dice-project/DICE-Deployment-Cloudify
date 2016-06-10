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


def process_library(library_path, platform, version, is_local):
    # Header
    template = os.path.join(library_path, "plugin.yaml")
    log("Processing '{}' ...".format(template))
    with open(template, "r") as input:
        library = yaml.load(input)

    # Place proper version inside header
    template = Template(library["plugins"]["dice"]["source"])
    library["plugins"]["dice"]["source"] = template.substitute(VERSION=version)

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

    return library


def save_output(library, output):
    output.write(yaml.dump(library, default_flow_style=False))


def main():
    script_path = os.path.dirname(os.path.realpath(__file__))
    library = os.path.realpath(os.path.join(script_path, "..", "library"))

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l", "--library", help="Library path (default: {})".format(library),
        default=library
    )
    parser.add_argument(
        "-o", "--output", help="Ouptut file location (default: stdout)",
        type=argparse.FileType("w"), default=sys.stdout
    )
    parser.add_argument(
        "platform", help="Platform for which library should be generated"
    )
    parser.add_argument(
        "version", help="Version name for which library should be generated"
    )
    parser.add_argument(
        "--local", help="Generate local plugin", action="store_true",
        default=False
    )
    args = parser.parse_args()

    library = process_library(args.library, args.platform, args.version,
                              args.local)
    save_output(library, args.output)


if __name__ == "__main__":
    main()
