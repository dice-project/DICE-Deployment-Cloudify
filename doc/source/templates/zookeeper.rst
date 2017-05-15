Apache Zookeeper
================

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
       type: dice.hosts.ubuntu.${HOST_SIZE}
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

Template variables
------------------

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

  HOST_SIZE
    Size of the host virtual machine. Available values are *Small*, *Medium*
    and *Large*.
