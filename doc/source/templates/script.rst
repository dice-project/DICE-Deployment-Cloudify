Script runner
-------------

Script runner can be used to perform user defined customizations on target
node.

.. code-block:: yaml

   node_templates:

     ${SCRIPT}:
       type: dice.components.misc.ScriptRunner
       properties:
         script: ${SCRIPT_LOCATION}
         language: ${SCRIPT_LANGUAGE}
         arguments: ${SCRIPT_ARGUMENTS}
         resources: ${SCRIPT_RESOURCES}
       relationships:
         - type: dice.relationships.ContainedIn
           target: ${TARGET_VM}

**Template variables:**

  SCRIPT
    Unique name for this script node.

  SCRIPT_LOCATION
    Relative path or URL of the script that should be run on the ${TARGET_VM}.
    If location is a relative path, script should be bundled with blueprint.

  SCRIPT_LANGUAGE
    Programming language in which script has been written. Supported values
    are *bash* and *python*.

  SCRIPT_ARGUMENTS
    Array of arguments that should be passed to script when being executed.

  SCRIPT_RESOURCES
    Array of relative paths and/or URLs that point to additional resources
    that should be copied to the same folder as main script.

  TARGET_VM
    Host on which script will be executed. This should be defined somewhere
    inside blueprint.
