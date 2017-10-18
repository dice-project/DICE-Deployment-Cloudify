Docker
======

DICE TOSCA library supports running docker containers as well as setting up
simple docker host. For the moment, we assume that all images that will be
used to create containers are public and hosted on docker hub.


Existing docker host
--------------------

Minimal blueprint that deploys selected image to preexisting docker host would
look like this:

.. code-block:: yaml

   node_templates:

     ${CONTAINER}:
       type: dice.components.docker.Container
       properties:
         host: ${DOCKER_HOST}
         image: ${IMAGE_NAME}
         tag: ${IMAGE_TAG}
         port_mapping:
           80/tcp: 9876
           81/tcp: null

Note that we need to set ``host`` property on the container, since there is no
relationships to connect container with docker host. It is also worth
mentioning that docker daemon should listen on tcp socket in order to be able
to serve as a host for DICE TOSCA library.


Create docker host
------------------

In order to deploy docker host, we need to prepare blueprint, similar to this:

.. code-block:: yaml

   node_templates:

     ${DOCKER}_ip:
       type: dice.VirtualIP

     ${DOCKER}_fw:
       type: dice.firewall_rules.docker.Server

     ${DOCKER}_fw_ephemeral:
       type: dice.firewall_rules.Base
       properties:
         rules:
           # Next rule covers most often used ephemeral port range on Linux.
           - ip_prefix: 0.0.0.0/0
             protocol: tcp
             from_port: 32768
             to_port: 61000

     ${DOCKER}_vm:
       type: dice.hosts.ubuntu.${HOST_SIZE}
       relationships:
         - type: dice.relationships.IPAvailableFrom
           target: ${DOCKER}_ip
         - type: dice.relationships.ProtectedBy
           target: ${DOCKER}_fw
         - type: dice.relationships.ProtectedBy
           target: ${DOCKER}_fw_ephemeral

     ${DOCKER}:
       type: dice.components.docker.Server
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${DOCKER}_vm

     ${CONTAINER}:
       type: dice.components.docker.Container
       properties:
         image: ${IMAGE_NAME}
         tag: ${IMAGE_TAG}
         port_mapping:
           80/tcp: 9876
           81/tcp: null
       relationships:
         - type: dice.relationships.docker.HostedOn
           target: ${DOCKER}

No ``host`` property needs to be set on the container in this case, since
relationship will properly connect the container to docker host. Installation
procedure also takes care of configuring docker daemon properly, so no manual
intervention is needed.


Template variables
------------------

  CONTAINER
    Name of the container we are creating.

  DOCKER_HOST
    Address of the docker host that will run this container.

  IMAGE_NAME
    Name of the image that should be used to create container.

  IMAGE_TAG
    Tag of the image that should be used to create container.

  DOCKER
    Name of the docker instance.

  HOST_SIZE
    Size of the VM instance that will host docker.
