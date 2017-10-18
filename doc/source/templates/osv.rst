OSv
===

DICE TOSCA library currently supports running OSv applications on OpenStack.
Minimalistic blueprint that runs a single application and exposes port 8000
can be produced from the following template:

.. code-block:: yaml

   node_templates:

     ${OSV_APPLICATION}_public_ip:
       type: dice.VirtualIP

     ${OSV_APPLICATION}_firewall:
       type: dice.firewall_rules.Base
       properties:
         rules:
           - ip_prefix: 0.0.0.0/0
             protocol: tcp
             port: 8000

     ${OSV_APPLICATION}:
       type: dice.components.osv.Application
       properties:
         instance_type: ${OPENSTACK_FLAVOR_ID}
         image: ${IMAGE_PATH_OR_URL}
         name: ${IMAGE_NAME}
         platform: openstack
       relationships:
         - type: dice.relationships.IPAvailableFrom
           target: ${OSV_APPLICATION}_public_ip
         - type: dice.relationships.ProtectedBy
           target: ${OSV_APPLICATION}_firewall


Template variables
------------------

  OSV_APPLICATION
    Name of the OSv application.

  OPENSTACK_FLAVOR_ID
    UUID of the flavor that should be used to create OSv application instance.

  IMAGE_PATH_OR_URL
    Path to the OSv application image. If this path is relative, orchestrator
    will expect image to be bundled inside a blueprint. If this is URL,
    orchestrator will download the image before trying to create it.

  IMAGE_NAME
    This is the name that will be assigned to the new image (this is what gets
    displayed in OpenStack management interface).
