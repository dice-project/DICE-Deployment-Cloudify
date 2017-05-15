Apache Hadoop
=============

Basic Hadoop cluster consists of name node, resource manager and a variable
number of worker nodes that run node manager and data node services.

.. code-block:: yaml

   node_templates:

     ${HADOOP}_namenode_firewall:
       type: dice.firewall_rules.hadoop.NameNode

     ${HADOOP}_namenode_vm:
       type: dice.hosts.ubuntu.${HOST_SIZE_NAMENODE}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${HADOOP}_namenode_firewall

     ${HADOOP}_namenode:
       type: dice.components.hadoop.NameNode
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${HADOOP}_namenode_vm

     ${HADOOP}_resourcemanager_firewall:
       type: dice.firewall_rules.hadoop.ResourceManager

     ${HADOOP}_resourcemanager_vm:
       type: dice.hosts.ubuntu.${HOST_SIZE_RESOURCEMANAGER}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${HADOOP}_resourcemanager_firewall

     ${HADOOP}_resourcemanager:
       type: dice.components.hadoop.ResourceManager
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${HADOOP}_resourcemanager_vm
         - type: dice.relationships.hadoop.ConnectedToNameNode
           target: ${HADOOP}_namenode

     ${HADOOP}_nodemanager_firewall:
       type: dice.firewall_rules.hadoop.NodeManager

     ${HADOOP}_datanode_firewall:
       type: dice.firewall_rules.hadoop.DataNode

     ${HADOOP}_worker_vm:
       type: dice.hosts.ubuntu.${HOST_SIZE_WORKER}
       instances:
         deploy: ${HADOOP_WORKER_COUNT}
       relationships:
         - type: dice.relationships.ProtectedBy
           target: ${HADOOP}_nodemanager_firewall
         - type: dice.relationships.ProtectedBy
           target: ${HADOOP}_datanode_firewall

     ${HADOOP}_nodemanager:
       type: dice.components.hadoop.NodeManager
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${HADOOP}_worker_vm
         - type: dice.relationships.hadoop.ConnectedToResourceManager
           target: ${HADOOP}_resourcemanager

     ${HADOOP}_datanode:
       type: dice.components.hadoop.DataNode
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${HADOOP}_worker_vm
         - type: dice.relationships.hadoop.ConnectedToNameNode
           target: ${HADOOP}_namenode

Template variables
------------------

  HADOOP
    The prefix that is used to make cluster names unique. If there is only a
    single cluster described in blueprint, this can be safely set to *hadoop*.

  HADOOP_WORKER_COUNT
    Number of Hadoop workers (data nodes and node managers) that should be
    created when creating cluster.

  HOST_SIZE_NAMENODE, HOST_SIZE_RESOURCEMANAGER, HOST_SIZE_WORKER
    Sizes of the virtual machines that host various parts of the Hadoop
    cluster. Available values are *Small*, *Medium* and *Large*.
