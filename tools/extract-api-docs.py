#!/usr/bin/env python

# Copyright (C) 2017 XLAB d.o.o.
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

from __future__ import print_function

import argparse
import re
import sys
import yaml


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


def process_fields(field_name, field_content, output):
    for name, definition in field_content.items():
        if "description" in definition:
            default = definition.get("default", "")
            if default:
                default = " (default: ``{}``)".format(default)
            output.write("  :{} {}: {}{}\n".format(
                field_name, name, definition["description"].strip(), default
            ))


def process_requirements(requirements, output):
    if requirements:
        rels = [":relationship:`{}`".format(r) for r in requirements]
        output.write("  :requirements: {}\n".format(", ".join(rels)))


def process_item(typ, name, definition, output):
    output.write(".. {}:: {}\n\n".format(typ, name))
    output.write("  {}\n\n".format(
        definition.get("description", "MISSING DESCRIPTION").strip()
    ))
    output.write("  :parent: :{}:`{}`\n".format(
        typ, definition["derived_from"]
    ))
    process_fields("property", definition.get("properties", {}), output)
    process_fields("attribute", definition.get("attributes", {}), output)
    process_requirements(definition.get("requirements", []), output)
    output.write("\n\n")


def process_components(node_types, output):
    components = [(k, v) for k, v in node_types.items()
                  if k.startswith("dice.components")]
    if components:
        output.write("Components\n"
                     "----------\n\n")
        for type_name, type_def in sorted(components, key=lambda x: x[0]):
            process_item("node_type", type_name, type_def, output)


def process_firewalls(node_types, output):
    components = [(k, v) for k, v in node_types.items()
                  if k.startswith("dice.firewall_rules")]
    if components:
        output.write("Firewall rules\n"
                     "--------------\n\n")
        for type_name, type_def in sorted(components, key=lambda x: x[0]):
            process_item("node_type", type_name, type_def, output)


def process_relationships(relationships, output):
    if relationships:
        output.write("Relationships\n"
                     "-------------\n\n")
        rels = sorted(list(relationships.items()), key=lambda x: x[0])
        for rel_name, rel_def in rels:
            process_item("relationship", rel_name, rel_def, output)


def process_intro(file, output):
    prefix_re = re.compile("^# ?")
    with open(file, "r") as input:
        for line in input:
            if not line.startswith("#"):
                output.write("\n\n")
                break
            output.write(prefix_re.sub("", line))


def process_file(file, output):
    log("Reading intro docs in comment ...")
    process_intro(file, output)

    log("Loading yaml {} ...".format(file))
    with open(file, "r") as input:
        defs = yaml.load(input)

    log("Processing components ...")
    process_components(defs.get("node_types", {}), output)

    log("Processing firewall rules ...")
    process_firewalls(defs.get("node_types", {}), output)

    log("Processing relationships ...")
    process_relationships(defs.get("relationships", {}), output)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-o", "--output", help="Ouptut file location", default=sys.stdout,
        type=argparse.FileType("w")
    )
    parser.add_argument("file", help="TOSCA definitions to extract docs from.")
    args = parser.parse_args()

    process_file(args.file, args.output)


if __name__ == "__main__":
    main()
