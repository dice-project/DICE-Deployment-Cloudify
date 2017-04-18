MongoDB
-------

DICE TOSCA library supports three MongoDB configurations: standalone,
replicated cluster and sharded cluster.

Standalone server is the simplest option. We only need a VM that will host the
mongo. By default, mongo installation does not allow unauthenticated access
and in order to start using the installation we need to define some databases
and users that can use the databases.

In the example below, we defined mongo instance with two databases that can be
used by user single user:

.. code-block:: yaml

   node_templates:

     ${MONGO}_firewall:
       type: dice.firewall_rules.mongo.Common

     ${MONGO}_vm:
       type: dice.hosts.ubuntu.${HOST_SIZE}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${MONGO}_firewall

     ${MONGO}:
       type: dice.components.mongo.Server
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${MONGO}_vm

     ${MONGO}_db1:
       type: dice.components.mongo.DB
       properties:
         name: ${MONGO_DB_NAME_1}
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${MONGO}

     ${MONGO}_db2:
       type: dice.components.mongo.DB
       properties:
         name: ${MONGO_DB_NAME_2}
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${MONGO}

     ${MONGO}_user:
       type: dice.components.mongo.User
       properties:
         username: ${MONGO_USER}
       relationships:
         - type: dice.relationships.mongo.HasRightsToUse
           target: ${MONGO}_db1
         - type: dice.relationships.mongo.HasRightsToUse
           target: ${MONGO}_db2
         - type: dice.relationships.ContainedIn
           target: ${MONGO}


Preparing replicated cluster is a bit more complicated, since we need to
inform orchestrator about mongo nodes that form a replicated set:

.. code-block:: yaml

   node_templates:

     ${MONGO}_firewall:
       type: dice.firewall_rules.mongo.Common

     ${MONGO}_vm:
       type: dice.hosts.ubuntu.${HOST_SIZE}
       instances:
         deploy: ${REPLICA_SERVER_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${MONGO}_firewall

     ${MONGO}:
       type: dice.components.mongo.ReplicaServer
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${MONGO}_vm

     ${MONGO}_replica_set:
       type: dice.components.mongo.Group
       relationships:
         - type: dice.relationships.mongo.ComposedOf
           target: ${MONGO}


Cluster setup that should be used in production environments where we expect
a heavy load should take advantage of sharding. Setting up such cluster is a
bit fiddly, but provided types should make preparing blueprint relatively
painless.

Sharded cluster consists of configuration servers, shard servers and
router(s) that are then connected into one cluster using DICE provided
relationships.

.. code-block:: yaml

   node_templates:

     ${MONGO}_firewall:
       type: dice.firewall_rules.mongo.Common

     ${MONGO}_config_vms:
       type: dice.hosts.ubuntu.{HOST_SIZE}
       instances:
         deploy: {CONFIG_SERVER_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${MONGO}_firewall

     ${MONGO}_config:
       type: dice.components.mongo.ConfigServer
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${MONGO}_config_vms

     ${MONGO}_config_replica:
       type: dice.components.mongo.Group
       relationships:
         - type: dice.relationships.mongo.ComposedOf
           target: ${MONGO}_config

     ${MONGO}_shard_1_vms:
       type: dice.hosts.ubuntu.{HOST_SIZE}
       instances:
         deploy: {SHARD_1_SERVER_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${MONGO}_firewall

     ${MONGO}_shard_1:
       type: dice.components.mongo.ShardServer
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${MONGO}_shard_1_vms

     ${MONGO}_shard_1_replica:
       type: dice.components.mongo.Group
       relationships:
         - type: dice.relationships.mongo.ComposedOf
           target: ${MONGO}_shard_1

     ${MONGO}_shard_2_vms:
       type: dice.hosts.ubuntu.{HOST_SIZE}
       instances:
         deploy: {SHARD_2_SERVER_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${MONGO}_firewall

     ${MONGO}_shard_2:
       type: dice.components.mongo.ShardServer
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${MONGO}_shard_2_vms

     ${MONGO}_shard_2_replica:
       type: dice.components.mongo.Group
       relationships:
         - type: dice.relationships.mongo.ComposedOf
           target: ${MONGO}_shard_2

     ${MONGO}_router_vm:
       type: dice.hosts.ubuntu.{HOST_SIZE}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${MONGO}_firewall

     ${MONGO}_router:
       type: dice.components.mongo.Router
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${MONGO}_router_vm
         - type: dice.relationships.mongo.ConfigurationStoredIn
           target: ${MONGO}_config_replica
         - type: dice.relationships.mongo.RoutesTo
           target: ${MONGO}_shard_1_replica
         - type: dice.relationships.mongo.RoutesTo
           target: ${MONGO}_shard_2_replica


**Template variables:**

  MONGO
    The name of the MongoDB cluster, usually set to *mongo*.

  REPLICA_SERVER_COUNT, SHARD_n_SERVER_COUNT, CONFIG_SERVER_COUNT
    Number of mongo workers that should be used to create
    replica/shard/configuration replica.

  MONGO_DB_NAME_n
    Name of the mongo database that should be created.

  MONGO_USER
    Name of the user that should be added to mongo.

  HOST_SIZE
    Size of the host virtual machine. Available values are *Small*, *Medium*
    and *Large*.
