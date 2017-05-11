Developer information
=====================

Main audience for this part of documentation are developers who would like to
and/or are being tasked to work on DICE TOSCA library.


Source code layout
------------------

Various TOSCA type definitions are stored inside ``library`` folder. The
``common`` folder hosts platform independent type definitions. Platform
dependent definitions should be placed inside ``PLATFORM.yaml`` file alongside
``common`` folder.

Layout of the ``common`` folder is free-form. Just make sure files with type
definitions inside end with ``.yaml`` and the tool that produces final,
"includable" plugin description will take care of traversing the folder
structure.

.. code-block:: none

   library
   ├── common
   │   ├── base.yaml
   │   ├── cassandra.yaml
   │   ├── mock.yaml
   │   ├── storm.yaml
   │   └── zookeeper.yaml
   ├── fco.yaml
   ├── openstack.yaml
   └── platform.yaml.template

Tasks that can be used in type definitions are defined inside ``dice_plugin``
python package. This is a standard python package, so if you ever worked on
package before, you should feel right at home.

Last component are the tools that take the various library files and produce
end results. Currently, there is only one tool, called ``gen-plugin-yaml.py``,
that takes complete library folder along with selected platform and produces
plugin definition that can be included in blueprints. For more information,
run script with no parameters and read help.


Developing plug-in
------------------

Plugin development should be done in feature branches. When the feature is
complete, feature branch should be rebased onto develop branch and then merge
request should be submitted.

When adding new functionality, it is useful to be able to test changes before
pushing anything to remote git repository. Assuming that we have a development
blueprint inside ``dev`` subfolder of the TOSCA library plugin, general steps
that need to be taken when doing off-line development are:

 #. Create new ``plugins`` subfolder inside ``dev``.
 #. Make changes to plugin and/or chef cookbooks.
 #. Create package zip and copy it to ``plugins`` subfolder.
 #. Create tarball of chef repo and copy it to ``dev`` folder.
 #. Generate local plugin description and use it in blueprint.
 #. Deploy blueprint.
 #. Go back to 1 because something went wrong;).

Commands that one usually executes during the session would look something
like this:

.. code-block:: bash

   mkdir -p dev/plugins
   # Do some developing
   rm -f dist/*.zip && python setup.py sdist --formats=zip
   cp dist/dice-plugin-*.zip dev/plugins/dice-plugin.zip
   tar -cvzf dev/repo.tar.gz -C /path/to/chef/repo --exclude=.git repo
   tools/gen-plugin-yaml.py -o dev/include.yaml -c repo.tar.gz \
     -d dice-plugin openstack # Or fco if testing is done on FCO
   cd dev
   cfy ... # Do cloduify testing of blueprint
   cd .. # Now go to line 2 and start again


Adding new platform to library
------------------------------

In order to make adding new platform to library as painless as possible,
``library/platform.yaml.template`` is provided that should serve as a starting
point for new platform. Make copy of this template, fill in details (replace
various Unimplemented placeholders).

Note that placeholders are designed in such a way that blueprint that simply
includes them will validate. Even more, as long as none of the Undefined types
is used at runtime, things will work as expected. This should make incremental
development more manageable.


Creating release
----------------

Tasks that need to be done when creating release are:

 #. Take note of Chef repo version that this release of library will use and
    get URl address of it's ``tar.gz`` archive (most likely Github download
    link).
 #. Make sure ``dice_plugin/__init__.py`` has proper version set.
 #. Open ``library/common/base.yaml`` file and update ``plugins.dice.source``
    field and
    ``node_types.dice.chef.SoftwareComponent.chef_config.default.chef_repo``
    field (this should point to Chef repo version that we took note in the
    first step of release task list).
 #. Merge develop branch into master.
 #. Tag the current git HEAD with proper version number.
 #. Publish generated plug-in description on Github pages hosting. This can be
    done most simply by copying existing spec and simply modifying link
    targets to new version of files. This will be automated soon-ish, but for
    now, we are stuck with this manual process.

Last step is a bit tricky, so we will just look at how to perform it with
relative ease. First, we need to get ``gh-pages`` branch checked out. You can
do this by cloning a separate copy of repo or by using ``git worktree``
command. Simply executing

.. code-block:: bash

   git worktree gh-pages gh-pages

will checkout ``gh-pages`` branch into ``gh-pages`` folder. Now create
subfolder with version name and do the link changing as described before.

One note about folder structure in ``gh-pages`` branch and where to place the
released plug-in yaml. We currently use
``/spec/<platform>/<version>/plugin.yaml`` template to structure releases.
Listing below shows two releases of OpenStack plug-in: 0.1.0 and develop.

.. code-block:: none

   gh-pages
   └── spec
       └── openstack
           ├── 0.1.0
           │   └── plugin.yaml
           └── develop
               └── plugin.yaml

Develop release is a special release that can be updated whenever developers
feel that ``develop`` branch is stable enough to warrant a development
release.


Generating docs
---------------

Documentation is generated using Sphinx, which means that it needs to be
installed first. The simplest way of installing it is to create new virtual
environment and execute ``pip install -r requirements-dev.txt``.
Documentation can now be generated by moving to ``doc`` folder and executing
``make html``.

Generated documentation can be viewed by pointing web browser to
``_build/html/index.html`` file.

Documentation can also be hosted on readthedocs_ page. Simply create new
account and add project. Additionally, one can setup more tight Github
integration that makes it possible to rebuild documentation when repo content
changes.

.. _readthedocs: https://readthedocs.org/


Reporting bugs
--------------

Visit `project's Github issues page`_ and file a bug.

.. _project's Github issues page:
   https://github.com/dice-project/DICE-Deployment-Cloudify/issues
