Quickstart
==========

In this kick-start document, we will write blueprint for minimalistic web
server using built-in mock server type.


Preprequisites
--------------

First, we will assume that we have Cloudify Manager installed and configured.
If this is not the case, consult official documentation on how to
`bootstrap the manager`_.

.. _bootstrap the manager:
   http://docs.getcloudify.org/3.4.0/manager/bootstrapping/


Writing blueprint
-----------------

Let us now write a simple blueprint that can be used to deploy minimalistic
web server that will serve static web page. First thing we need to do is
define ``tosca_definitions_version`` and import plugins that we will be using.

.. literalinclude:: ../examples/hello-openstack.yaml
   :language: yaml
   :lines: 1-4

All blueprints need the imports section - this is where basic type definitions
are found. Since we are preparing blueprint for OpenStack, we included
OpenStack plugin that will make sure we can create new virtual machines. If
you wish to deploy to FCO, simply replace ``openstack`` in URL with ``fco``.

Next section of the blueprint specifies actually topology of our application.
In our example, topology is simple and consists of:

 * single virtual machine to host web server (*vm*),
 * actual web server (*server*),
 * virtual ip that allows us to access virtual machine from outside and
 * firewall that protects the whole thing.

All of the predefined types have all of their properties set to sane default
values, which makes it easy to start writing blueprints. In our case, we only
need to list all four nodes that are present in deployment and connect them
using relationships.

.. literalinclude:: ../examples/hello-openstack.yaml
   :language: yaml
   :lines: 6-25

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

.. code-block:: bash

   cfy blueprint upload -p hello-openstack.yaml -b hello
   cfy deployments create -b hello -d hello -i inputs.openstack
   cfy executions start -w install -d hello -l

After a couple of minutes, we should have our server up. Tearing it down is
again simple. Executing

.. code-block:: bash

   cfy executions start -w uninstall -d hello -l
   cfy deployments delete -d hello
   cfy blueprints delete -b hello

And that is basically all there is to creating and deploying simple static web
server. For more examples visit `Github repo with examples`_.

.. _Github repo with examples:
   https://github.com/dice-project/DICE-Deployment-Examples
