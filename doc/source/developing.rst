Developer information
=====================

Main audience for this part of documentation are developers who would like to
and/or are being tasked to work on DICE TOSCA library.


Source code layout
------------------

Various TOSCA type definitions are stored inside :file:`library` folder.
Platform dependent definitions should be placed inside :file:`PLATFORM.yaml`.

Layout of the :file:`library` folder is free-form. Just make sure files with
type definitions inside end with ``.yaml`` and the tool that produces final,
"includable" plugin description will take care of traversing the folder
structure::

   library
   ├── base.yaml
   ├── cassandra.yaml
   ├── mock.yaml
   ├── storm.yaml
   ├── ...
   ├── fco.yaml
   ├── openstack.yaml
   └── zookeeper.yaml

Tasks that can be used in type definitions are defined inside
:file:`dice_plugin` python package. This is a standard python package, so if
you ever worked on package before, you should feel right at home.

Last component are the tools that take the various library files and produce
end results. Currently available tools are:

:program:`gen-plugin-yaml.py`
   Tool that takes complete library folder as an input and produces plugin
   definition that can be included in blueprints. For more information, run
   script with no parameters and read help text.

:program:`extract-api-docs.py`
   Tool that takes yaml file with TOSCA definitions as an input and produces
   API docs that can be included in final documentation.


Developing plug-in
------------------

Plugin development should be done in feature branches. When the feature is
complete, feature branch should be rebased onto develop branch and then merge
request should be submitted.

When adding new functionality, it is useful to be able to test changes before
pushing anything to remote git repository. Assuming that we have a development
blueprint inside :file:`dev` subfolder of the TOSCA library plugin, general
steps that need to be taken when doing off-line development are:

 #. Create new :file:`plugins` subfolder inside :file:`dev`.
 #. Make changes to plugin and/or chef cookbooks.
 #. Create package zip and copy it to :file:`plugins` subfolder.
 #. Create tarball of chef repo and copy it to :file:`dev` folder.
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
   tools/gen-plugin-yaml.py -o dev/include.yaml chef.tar.gz dice-plugin
   cd dev
   cfy ... # Do cloduify testing of blueprint
   cd .. # Now go to line 2 and start again


Adding new platform to library
------------------------------

In order to make adding new platform to library as painless as possible,
simply copy the :file:`dice_plugin/openstack.py` and adapt the function
definitions. In order to register new platform, open
:file:`dice_plugn/general.py` and add new platform to ``PLATFORMS``
dictionary. Last thing is to add any additional libraries to
:file:`requirements.txt` file.


Creating release
----------------

Tasks that need to be done when creating release are:

 #. Take note of Chef repo version that this release of library will use and
    get URl address of it's ``tar.gz`` archive (most likely Github download
    link).
 #. Tag the current git HEAD with proper version number and prepare Github
    release.
 #. Prepare python package by running ``python setup.py sdist --formats=zip``.
 #. Upload produced package to the Github release page and take note of the
    url that serves the uploaded zip.
 #. Generate lite library import by running
    ``tools/gen-plugin-yaml.py --lite -o lite.yaml CHEF_URL LIB_URL``, where
    ``CHEF_URL`` is the address that we took note of in step 1 and ``LIB_URL``
    is the address of the uploaded zip file from step 4.
 #. Generate full library import by running
    ``tools/gen-plugin-yaml.py -o full.yaml CHEF_URL LIB_URL``, where
    ``CHEF_URL`` is the address that we took note of in step 1 and ``LIB_URL``
    is the address of the uploaded zip file from step 4.
 #. Publish generated plug-in descriptions on Github release page.


Generating docs
---------------

Parts of the documentation are extracted from library definitions and needs to
be placed into proper place before we gan generate the final document. In
order to extract the docs, we must run:

.. code-block:: bash

   rm -rf doc/source/api
   mkdir doc/source/api
   for comp in library/*.yaml
   do
     tools/extract-api-docs.py $comp -o doc/source/api/$(basename $comp yaml)rst
   done

Documentation is generated using Sphinx, which means that it needs to be
installed first. The simplest way of installing it is to create new virtual
environment and execute ``pip install -r requirements-dev.txt``.
Documentation can now be generated by running
:command:`python setup.py build_sphinx`.

Generated documentation can be viewed by pointing web browser to
:file:`doc/build/html/index.html` file.

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
