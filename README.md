# DICE TOSCA library

DICE TOSCA library is a Cloudify plugin that eases the process of writing
blueprints for various providers with minimal changes.


## Sample blueprint for minimalistic web server

First, we will assume that we have Cloudify Manager installed and configured
on OpenStack. If this is not the case, consult official documentation on how
to [bootstrap the manager][cfy-mng-boot].

[cfy-mng-boot]: http://docs.getcloudify.org/3.3.1/manager/bootstrapping/


Let us write a simple blueprint that can be used to deploy minimalistic web
server that will serve static web page. First thing we need to do is write
down `tosca_definitions_version` and import plugins that we will be using.

    tosca_definitions_version: cloudify_dsl_1_2
    imports:
      - http://www.getcloudify.org/spec/cloudify/3.3.1/types.yaml
      - http://dice-project.github.io/cloudify-openstack-plugin/1.4/plugin.yaml
      - http://dice-project.github.io/cloudify-chef-plugin/1.3.2/plugin.yaml
      - http://dice-project.github.io/DICE-Deployment-Cloudify/spec/openstack/0.1.3/plugin.yaml

All blueprints need the first import - this is where basic types are defined.
Since we are preparing blueprint for OpenStack, we included OpenStack plugin
that will make sure we can create new virtual machines. The last import is our
DICE library that included wide variety of predefined types (to be honest, at
the moment, only demo server types are fully functional, but there are others
in the works).

Next thing we need to provide is inputs section, where we declare variable
parts of the types. The contents of this section is actually fixed when we use
DICE library, but due to current limitation of Cloudify DSL that only allows
inputs to be declared in the blueprint, we need to manually add it to the
blueprint. All of the inputs are related to OpenStack image in flavor IDs and
should be reasonably clear to anyone who used OpenStack before.

```
inputs:
  agent_user:
    default: ubuntu
  small_image_id:
    default: 36dbc4e8-81dd-49f5-9e43-f44a179a64ea
  small_flavor_id:
    default: 070005dc-9bd5-4c0c-b2c6-88f81a7b7239
  medium_image_id:
    default: 36dbc4e8-81dd-49f5-9e43-f44a179a64ea
  medium_flavor_id:
    default: 070005dc-9bd5-4c0c-b2c6-88f81a7b7239
  large_image_id:
    default: 36dbc4e8-81dd-49f5-9e43-f44a179a64ea
  large_flavor_id:
    default: 070005dc-9bd5-4c0c-b2c6-88f81a7b7239
```

It is in the last section of the blueprint that we specify actually topology
of our application. In our example, topology is simple and consists of:

 * single virtual machine to host web server (_vm_)
 * actual web server (server)
 * floating ip that allows us to access virtual machine from outside
 * firewall that protects the whole thing

All of the predefined types have all of their properties set to sane default
values, which makes it easy to start writing blueprints. In our case, we only
need to define all four nodes that are present in deployment and connect them
using relationships.

Note that most of the types and relationships are from dice namespace, but no
virtual_ip. Because floating ip is OpenStack specific thing, we did not try to
wrap it in dice library.

```
node_templates:
  virtual_ip:
    type: cloudify.openstack.nodes.FloatingIP

  firewall:
    type: dice.firewall_rules.mock.WebServer

  vm:
    type: dice.hosts.Small
    relationships:
      - type: dice.relationships.ProtectedBy
        target: firewall
      - type: cloudify.openstack.server_connected_to_floating_ip
        target: virtual_ip

  server:
    type: dice.components.mock.WebServer
    relationships:
      - type: dice.relationships.ContainedIn
        target: vm
```

And that is basically all that we need to write. Complete blueprint (with some
additional stuff that is not directly relevant to our goal of getting
something up and running) is available in examples folder.

Deploying our server is now as simple as

    cfy blueprint upload -p hello-openstack.yaml -b hello
    cfy deployments create -b hello -d hello
    cfy executions start -w install -d hello -l

After a couple of minutes, we should have our server up. Tearing it down is
again simple. Executing

    cfy executions start -w uninstall -d hello -l
    cfy deployments delete -d hello
    cfy blueprints delete -b hello

And that is basically all there is to creating and deploying simple static web
server.


## Developer information

Various TOSCA type definitions are stored inside `library` folder. In there,
there is a `common` folder that hosts platform independent type definitions
and a `plugin.yaml` file that holds metadata about the plugin. Platform
dependent definitions should be placed inside `platform.yaml` file alongside
`common` folder.

Layout of the `common` folder is free-form. Just make sure files with type
definitions inside end with `.yaml` and the tool that produces final,
"includable" plugin description will take care of traversing the folder
structure.

    library
    ├── common
    │   ├── base.yaml
    │   ├── cassandra.yaml
    │   ├── mock.yaml
    │   ├── storm.yaml
    │   └── zookeeper.yaml
    ├── fco.yaml
    ├── openstack.yaml
    └── platform.yaml.template

Tasks that can be used in type definitions are defined inside `dice_plugin`
python package. This is a standard python package, so if you ever worked on
package before, you should feel right at home.

Last component are the tools that take the various library files and produce
end results. Currently, there is only one tool, called `gen-plugin-yaml.py`,
that takes complete library folder along with selected platform and produces
plugin definition that can be included in blueprints. For more information,
run script with no parameters and read help.


### Developing plug-in

Plugin development should be done in feature branches. When the feature is
complete, feature branch should be rebased onto develop branch and then merge
request should be submitted.

When adding new functionality, it is useful to be able to test changes before
pushing anything to remote git repository. Assuming that we have a development
blueprint inside `dev` subfolder of the TOSCA library plugin, general steps
that need to be taken when doing off-line development are:

 0. Create new `plugins` subfolder inside `dev`.
 1. Make changes to plugin and/or chef cookbooks.
 2. Create package zip and copy it to `plugins` subfolder.
 3. Create tarball of chef repo and copy it to `dev` folder.
 5. Generate local plugin description and use it in blueprint.
 6. Deploy blueprint.
 7. Go back to 1 because something went wrong;).

Commands that one usually executes during the session would look something
like this:

    $ mkdir dev/plugins
    $ # Do some developing
    $ rm -f dist/*.zip && python setup.py sdist --formats=zip
    $ cp dist/dice-plugin-*.zip dev/plugins/dice-plugin.zip
    $ tar -cvzf dev/repo.tar.gz -C /path/to/chef/repo --exclude=.git repo
    $ tools/gen-plugin-yaml.py -o dev/include.yaml -c repo.tar.gz \
        -d dice-plugin openstack # Or FCO if testing is done on FCO
    $ cd dev
    $ cfy ... # Do cloduify testing of blueprint
    $ cd .. # Now go to line 2 and start again


## Adding new platform to library

In order to make adding new platform to library as painless as possible,
`library/platform.yaml.template` is provided that should serve as a starting
point for new platform. Make copy of this template, fill in details (replace
various Unimplemented placeholders).

Note that placeholders are designed in such a way that blueprint that simply
includes them will validate. Even more, as long as none of the Undefined types
is used at runtime, things will work as expected. This should make incremental
development more manageable.


### Creating release

Tasks that need to be done when creating release are:

 0. Make sure `dice_plugin/__init__.py` has proper version set.
 1. Merge develop branch into master.
 2. Tag the current git HEAD with proper version number.
 3. Run `gen-plugin-yaml.py` script with proper platform
    information to produce includable plug-in description.
 4. Publish generated plug-in description on Github pages hosting.

First four commands are easy, so we will just look at how to properly do the
last point. First, we need to get `gh-pages` branch checked out. You ca do
this by cloning a separate copy of repo or by using `git worktree` command.
Simply executing

    $ git worktree gh-pages gh-pages

will checkout `gh-pages` branch into `gh-pages` folder. Now create subfolder
with version name and place file, generated in step three, into this folder.
Commit changes and push branch.

One note about folder structure in `gh-pages` branch and where to place the
released plug-in yaml. We currently use
`/spec/<platform>/<version>/plugin.yaml` template to structure releases.
Listing below shows two releases of OpenStack plug-in: 0.1.0 and develop.

    gh-pages
    └── spec
        └── openstack
            ├── 0.1.0
            │   └── plugin.yaml
            └── develop
                └── plugin.yaml

Develop release is a special release that can be updated whenever developers
feel that `develop` branch is stable enough to warrant a development release.


### Reporting bugs

Since currently, this is a small, one developer project, just find my email
somewhere inside the sources and contact me directly.
