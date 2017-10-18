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


def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def merge(a, b):
    """
    Merge dicts a and b recursively
    """
    for k in b.keys():
        if isinstance(b[k], dict) and k in a and isinstance(a[k], dict):
            merge(a[k], b[k])
        elif isinstance(b[k], list) and k in a and isinstance(a[k], list):
            # Merge lists while removing duplicates (if we need to preserve
            # order, simply casting things to set will ot work).
            a[k] = list(set(a[k]) | set(b[k]))
        elif k not in a:
            a[k] = b[k]
        else:
            raise ValueError("Duplicated key: {}".format(k))


def remove_unsupported_fields(library):
    def clean(node):
        node.pop("description", None)
        node.pop("attributes", None)
        node.pop("requirements", None)

    for node_type in library.get("node_types", {}).values():
        clean(node_type)
    for rel_type in library.get("relationships", {}).values():
        clean(rel_type)


def process_library(library_path, chef_tar, package, lite):
    library = {}

    if lite:
        items = ("platform.yaml", "openstack.yaml", "fco.yaml", "aws.yaml",
                 "docker", "osv.yaml")
    else:
        items = (f for f in os.listdir(library_path) if f.endswith(".yaml"))
    yamls = (os.path.join(library_path, f) for f in items)

    for y in yamls:
        log("Processing '{}' ...".format(y))
        with open(y, "r") as input:
            merge(library, yaml.load(input))

    if not lite:
        log("Inserting Chef repo location ...")
        library["inputs"]["chef_repo"]["default"] = chef_tar

    log("Inserting plugin package location ...")
    library["plugins"]["dice"]["source"] = package

    remove_unsupported_fields(library)

    return library


def save_output(library, output):
    output.write(yaml.dump(library, default_flow_style=False))


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-l", "--library", help="Library path", default="library"
    )
    parser.add_argument(
        "-o", "--output", help="Ouptut file location", default=sys.stdout,
        type=argparse.FileType("w")
    )
    parser.add_argument("--lite", help="Produce lite library import",
                        action="store_true", default=False)
    parser.add_argument("chef", help="URL of Chef repo tar.gz. release")
    parser.add_argument("package", help="URL to DICE TOSCA repo package.")
    args = parser.parse_args()

    library = process_library(args.library, args.chef, args.package, args.lite)
    save_output(library, args.output)


if __name__ == "__main__":
    main()
