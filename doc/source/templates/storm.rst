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
       type: dice.hosts.ubuntu.${HOST_SIZE_NIMBUS}
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
           target: ${ZOOKEEPER}_quorum

     ${STORM}_worker_firewall:
       type: dice.firewall_rules.storm.Worker

     ${STORM}_worker_vm:
       type: dice.hosts.ubuntu.${HOST_SIZE_WORKER}
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

  HOST_SIZE_NIMBUS, HOST_SIZE_WORKER
    Sizes of the nimbus and worker virtual machines. Available values are
    *Small*, *Medium* and *Large*.
