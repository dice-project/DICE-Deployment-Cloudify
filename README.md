# DICE TOSCA library

DICE TOSCA library is a Cloudify plugin that eases the process of writing
blueprints for various providers with minimal changes.


## Sample blueprint for minimalistic web server

First, we will assume that we have Cloudify Manager installed and configured.
If this is not the case, consult official documentation on how to
[bootstrap the manager][cfy-mng-boot].

[cfy-mng-boot]: http://docs.getcloudify.org/3.4.0/manager/bootstrapping/


Let us write a simple blueprint that can be used to deploy minimalistic web
server that will serve static web page. First thing we need to do is write
down `tosca_definitions_version` and import plugins that we will be using.

    tosca_definitions_version: cloudify_dsl_1_3
    imports:
      - http://dice-project.github.io/DICE-Deployment-Cloudify/spec/openstack/0.2.1/plugin.yaml

All blueprints need the imports section - this is where basic type definitions
are found. Since we are preparing blueprint for OpenStack, we included
OpenStack plugin that will make sure we can create new virtual machines. If
you wish to deploy to FCO, simply replace `openstack` in URL with `fco`.

Next section of the blueprint specifies actually topology of our application.
In our example, topology is simple and consists of:

 * single virtual machine to host web server (_vm_)
 * actual web server (server)
 * floating ip that allows us to access virtual machine from outside
 * firewall that protects the whole thing

All of the predefined types have all of their properties set to sane default
values, which makes it easy to start writing blueprints. In our case, we only
need to define all four nodes that are present in deployment and connect them
using relationships.

```
node_templates:
  virtual_ip:
    type: dice.VirtualIP

  firewall:
    type: dice.firewall_rules.mock.WebServer

  vm:
    type: dice.hosts.Small
    relationships:
      - type: dice.relationships.ProtectedBy
        target: firewall
      - type: dice.relationships.IPAvailableFrom
        target: virtual_ip

  server:
    type: dice.components.mock.WebServer
    relationships:
      - type: dice.relationships.ContainedIn
        target: vm
```

And that is basically all that we need to write. Complete blueprints (with some
additional stuff that is not directly relevant to our goal of getting
something up and running) are available in examples folder for OpenStack and
FCO platforms.

Last thing before we can attempt to deploy our server is to prepare some
inputs. TOSCA types that are defined by this library require some
configuration in order to be able to use them on various platforms. There are
input files present in example folder that should server as a reference and
starting point.

Deploying our server is now as simple as

    cfy blueprint upload -p hello-openstack.yaml -b hello
    cfy deployments create -b hello -d hello -i inputs.openstack
    cfy executions start -w install -d hello -l

After a couple of minutes, we should have our server up. Tearing it down is
again simple. Executing

    cfy executions start -w uninstall -d hello -l
    cfy deployments delete -d hello
    cfy blueprints delete -b hello

And that is basically all there is to creating and deploying simple static web
server. For more examples visit [Github repo with examples][examples].

[examples]: https://github.com/dice-project/DICE-Deployment-Examples


## Developer information

Various TOSCA type definitions are stored inside `library` folder. The
`common` folder hosts platform independent type definitions. Platform
dependent definitions should be placed inside `PLATFORM.yaml` file alongside
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

Visit [project's Github issues page][issues] and file a bug.

[issues]: https://github.com/dice-project/DICE-Deployment-Cloudify/issues
