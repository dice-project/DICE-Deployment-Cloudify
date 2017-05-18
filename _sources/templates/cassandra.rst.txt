Apache Cassandra
================

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
       type: dice.hosts.ubuntu.${HOST_SIZE}
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
       type: dice.hosts.ubuntu.${HOST_SIZE}
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

Template variables
------------------

  CASSANDRA
    The name of the Cassandra cluster, usually set to *cassandra*.

  CASSANDRA_CONFIGURATION
    A dictionary containing the configuration of the `${CASSANDRA}` cluster.
    If no special configuration is needed, use ``{}`` here.

  CASSANDRA_INSTANCE_COUNT
    Number of Cassandra workers that we would like to deploy as part of this
    cluster.

  HOST_SIZE
    Size of the host virtual machine. Available values are *Small*, *Medium*
    and *Large*.
