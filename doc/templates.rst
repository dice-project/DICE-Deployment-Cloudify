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


Apache Zookeeper
----------------

In order to setup Zookeeper cluster, we need to prepare virtual machines and
group them into quorum. We need to do this because Zookeeper insists on having
all members of cluster known in advance and having quorum neatly solves this
issue.

Emphasized lines can be removed from final blueprint if template variables
have their default value.

.. code-block:: yaml

   node_templates:

     ${ZOOKEEPER}_firewall:
       type: dice.firewall_rules.zookeeper.Server

     ${ZOOKEEPER}_vm:
       type: dice.hosts.Medium
       instances:
         deploy: ${ZOOKEEPER_INSTANCE_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${ZOOKEEPER}_firewall

     ${ZOOKEEPER}_quorum:
       type: dice.components.zookeeper.Quorum
       relationships:
         - type: dice.relationships.zookeeper.QuorumContains
           target: ${ZOOKEEPER}_vm

     ${ZOOKEEPER}:
       type: dice.components.zookeeper.Server
       properties:
         configuration: ${ZOOKEEPER_CONFIGURATION}
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${ZOOKEEPER}_vm
         - type: dice.relationships.zookeeper.MemberOfQuorum
           target: ${ZOOKEEPER}_quorum

**Template variables:**

  ZOOKEEPER
    The name of the Zookeeper instance. This is usually set to *zookeeper* or
    something similar.

  ZOOKEEPER_INSTANCE_COUNT
    Number of Zookeeper instances that should be in the cluster. This should
    be set to some odd number (3 and 5 are popular and safe choices for
    production environments). For testing purposes, setting this to 1 is
    acceptable.

  ZOOKEEPER_CONFIGURATION
    A dictionary containing the configuration for the Zookeeper instance. For
    valid values consult Zookeeper's documentation. If no custom configuration
    is needed (as is the case most of the time), set this property to empty
    dictionary ``{}``.
    Example::

      configuration:
        tickTime: 1500
        initLimit: 10
        syncLimit: 5


Apache Storm
------------

Before we can deploy Storm cluster, we need to have access to Zookeeper
quorum, since Storm stores most of it's configuration there. In this template,
we will assume that Zookeeper cluster is already defined and available to us.

If we only wish to prepare cluster without submitting any jobs,
``${STORM_TOPOLOGY}`` parts of the template can be removed, along with it's
associated output fragment.

.. code-block:: yaml

   node_templates:

     ${STORM}_nimbus_firewall:
       type: dice.firewall_rules.storm.Nimbus

     ${STORM}_virtual_ip:
       type: dice.VirtualIP

     ${STORM}_nimbus_vm:
       type: dice.hosts.Medium
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${STORM}_nimbus_firewall
         - type: dice.relationships.IpAvailableFrom
           target: ${STORM}_virtual_ip

     ${STORM}_nimbus:
       type: dice.components.storm.Nimbus
       properties:
         configuration: ${STORM_CONFIGURATION}
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${STORM}_nimbus_vm
         - type: dice.relationships.storm.ConnectedToZookeeperQuorum
           target: zookeeper_quorum

     ${STORM}_worker_firewall:
       type: dice.firewall_rules.storm.Worker

     ${STORM}_worker_vm:
       type: dice.hosts.Medium
       instances:
         deploy: ${STORM_INSTANCE_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${STORM}_worker_firewall

     ${STORM}_worker:
       type: dice.components.storm.Worker
       properties:
         configuration: ${STORM_CONFIGURATION}
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${STORM}_worker_vm
         - type: dice.relationships.storm.ConnectedToZookeeperQuorum
           target: ${ZOOKEEPER}_quorum
         - type: dice.relationships.storm.ConnectedToNimbus
           target: ${STORM}_nimbus

     ${STORM_TOPOLOGY}:
       type: dice.components.storm.Topology
       properties:
         application: ${STORM_TOPOLOGY_JAR_LOCATION}
         topology_name: ${STORM_TOPOLOGY_NAME}
         topology_class: ${STORM_TOPOLOGY_CLASS}
         configuration: ${STORM_TOPOLOGY_CONFIGURATION}
      relationships:
        - type: dice.relationships.storm.SubmitTopologyFromVM
          target: ${STORM}_nimbus_vm
        - type: dice.relationships.Needs
          target: ${STORM}

   outputs:

     ${STORM}_nimbus_address:
       description: Nimbus address as used by storm client.
       value:
         get_attribute: [ ${STORM}_virtual_ip, virtual_ip ]

     ${STORM}_nimbus_gui:
       description: URL of the Storm nimbus gui of "${STORM}"
       value:
         concat:
           - 'http://'
           - get_attribute: [ ${STORM}_virtual_ip, virtual_ip]
           - ':8080'

     ${STORM_TOPOLOGY}_id:
       description: Unique Storm topology ID for "${STORM_TOPOLOGY}"
       value:
         get_attribute: [ ${STORM_TOPOLOGY}, topology_id ]

**Template variables:**

  ZOOKEEPER
    The name of the Zookeeper cluster that this Storm cluster will use.

  STORM
    The name of the Storm cluster. Usually, this is set to *storm* for the
    sake of simplicity.

  STORM_CONFIGURATION
    A dictionary containing the configuration of the ``${STORM}`` instance.

  STORM_INSTANCE_COUNT
    Number of Storm worker instances to deploy.

  STORM_TOPOLOGY
    The name of the Storm topology. Can be anything, but general advice is to
    set to something that describes functionality of the topology being
    submitted.

  STORM_TOPOLOGY_JAR_LOCATION
   The URL or the filename where the user's Storm topology can be obtained. If
   the location starts with a protocol designation such as 'https', then the
   jar needs to be available for download from the provided URL. If no
   protocol designation is provided, the deployment tools assume a file
   packaged with the blueprint.

  STORM_TOPOLOGY_NAME
    The name of the user's Storm topology as it will be used in the Storm.

  STORM_TOPOLOGY_CLASS
    The class name with the main function, which implements the Storm
    topology.

  STORM_TOPOLOGY_CONFIGURATION
    A dictionary containing the configuration that will be used when
    submitting the topology jar to the nimbus. If no special configuration is
    needed, use ``{}`` here.


Apache Cassandra
----------------

Supported Cassandra cluster is composed of a single seed node and arbitrary
many worker nodes that all initially connect to seed node.

.. note::

   In the future, the limitation of supporting only one seed per cluster will
   be lifted and single point of failure at the start will be eliminated.

.. code-block:: yaml

   node_templates:

     ${CASSANDRA}_seed_firewall:
       type: dice.firewall_rules.cassandra.Seed

     ${CASSANDRA}_seed_vm:
       type: dice.hosts.Medium
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${CASSANDRA}_seed_firewall

     ${CASSANDRA}_seed:
       type: dice.components.cassandra.Seed
       properties:
         configuration: ${CASSANDRA_CONFIGURATION}
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${CASSANDRA}_seed_vm

     ${CASSANDRA}_worker_firewall:
       type: dice.firewall_rules.cassandra.Worker

     ${CASSANDRA}_worker_vm:
       type: dice.hosts.Medium
       instances:
         deploy: ${CASSANDRA_INSTANCE_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${CASSANDRA}_worker_firewall

     ${CASSANDRA}_worker:
       type: dice.components.cassandra.Worker
       properties:
         configuration: ${CASSANDRA_CONFIGURATION}
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${CASSANDRA}_seed_vm
         - type: dice.relationships.cassandra.ConnectedToSeed
           target: ${CASSANDRA}_seed

**Template variables:**

  CASSANDRA
    The name of the Cassandra cluster, usually set to *cassandra*.

  CASSANDRA_CONFIGURATION
    A dictionary containing the configuration of the `${CASSANDRA}` cluster.
    If no special configuration is needed, use ``{}`` here.

  CASSANDRA_INSTANCE_COUNT
    Number of Cassandra workers that we would like to deploy as part of this
    cluster.


Apache Spark (standalone)
-------------------------

Using Apache Spark in standalone mode is quite simple. We need to have one
Spark master node and multiple Spark worker nodes. Spark jobs are separate
node that related to master and worker nodes (master will submit this
application, worker relationships are only there for ordering - we do not want
to submit Spark job into partially prepared cluster).

.. code-block:: yaml

   node_templates:

     ${SPARK}_master_firewall:
       type: dice.firewall_rules.spark.Master

     ${SPARK}_master_vm:
       type: dice.hosts.Medium
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${SPARK}_master_firewall

     ${SPARK}_master:
       type: dice.components.spark.Master
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${SPARK}_master_vm

     ${SPARK}_worker_firewall:
       type: dice.firewall_rules.spark.Worker

     ${SPARK}_worker_vm:
       type: dice.hosts.Medium
       instances:
         deploy: ${SPARK_WORKER_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${SPARK}_worker_firewall

     ${SPARK}_worker:
       type: dice.components.spark.Worker
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${SPARK}_worker_vm
         - type: dice.relationships.spark.ConnectedToMaster
           target: ${SPARK}_master

     ${SPARK_JOB}:
       type: dice.components.spark.Application
       properties:
         jar: ${SPARK_JOB_JAR_LOCATION}
         class: ${SPARK_JOB_CLASS}
         name: ${SPARK_JOB_NAME}
         args: ${SPARK_JOB_ARGUMENTS}
       relationships:
         - type: dice.relationships.spark.SubmittedBy
           target: ${SPARK}_master
         - type: dice.relationships.Needs
           target: ${SPARK}_worker

**Template variables:**

  SPARK
    The name of the Spark cluster. This is usually set to *spark*, which gives
    us *spark_master* and *spark_worker* nodes.

  SPARK_WORKER_COUNT
    Number of Spark worker instances that should be created when deploying
    cluster.

  SPARK_JOB
    The name of the Spark job that we wish to submit.

  SPARK_JOB_JAR_LOCATION
    Location of the Spark job jar. This can be either URL or relative path, in
    which case jar needs to be bundled with blueprint.

  SPARK_JOB_CLASS
    Name of the class that should be executed when submitting Spark job.

  SPARK_JOB_NAME
    Name that should be used for application when jar is submitted. This name
    can be seen in Spark UI.

  SPARK_JOB_ARGUMENTS
    Array of arguments that should be passed to jar when being submitted. If
    application takes no additional arguments, set this to ``[]``.
