Blueprint generation templates
==============================

This part of documentation contains the templates for generating TOSCA
documents, which work with DICE Deployment Service. In this context, the word
"template" means a string of text with interchangeable variables.

The TOSCA blueprint is composed of several parts (version definition, imports,
node templates, outputs, etc.), the contents of which depend on the platform
used and the technologies appearing in the blueprint. Conversely, this
document presents relevant parts of the templates.

In each section, there are the mandatory contents, which all have to be in
place for the blueprint to work. Optional parts depend on the users'
preferences.


Common parts
------------

Each blueprint needs to have a header section where language version is
specified and proper DICE TOSCA library plugin description is imported.

.. code-block:: yaml

   tosca_definitions_version: cloudify_dsl_1_3

   imports:
     - http://dice-project.github.io/DICE-Deployment-Cloudify/spec/${PLATFORM}/${LIBRARY_VERSION}/plugin.yaml

**Template variables**

  PLATFORM
    Specifies the platform to deploy the application to. Currently supported
    platforms are *fco* and *openstack*.

  LIBRARY_VERSION
    Specifies the version of the plugin containing the DICE technology library
    definitions.


.. include:: templates/cassandra.rst
.. include:: templates/spark.rst
.. include:: templates/storm.rst
.. include:: templates/zookeeper.rst
