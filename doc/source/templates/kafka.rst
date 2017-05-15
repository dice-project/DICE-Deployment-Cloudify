Apache Kafka
============

Before we can deploy Kafka cluster, we need to have access to Zookeeper
cluster. we will assume in this template that Zookeeper quorum is already
defined somewhere in blueprint.

.. code-block:: yaml

   node_templates:

     ${KAFKA}_firewall:
       type: dice.firewall_rules.kafka.Broker

     ${KAFKA}_vm:
       type: dice.hosts.ubuntu.${HOST_SIZE}
       instances:
         deploy: ${KAFKA_INSTANCE_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${KAFKA}_firewall

     ${KAFKA}:
       type: dice.components.kafka.Broker
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${KAFKA}_vm
         - type: dice.relationships.zookeeper.ConnectedToZookeeperQuorum
           target: ${ZOOKEEPER}_quorum

Template variables
------------------

  KAFKA
    Unique name of the Kafka cluster. If there is a single Kafka cluster
    described in blueprint, this can be set to anything, but usually to
    *kafka*.

  KAFKA_INSTANCE_COUNT
    Number of Kafka brokers to include in cluster.

  ZOOKEEPER
    Name of the Zookeeper cluster that should be used by Kafka to coordinate
    work between worker instances.

  HOST_SIZE
    Size of the host virtual machine. Available values are *Small*, *Medium*
    and *Large*.
