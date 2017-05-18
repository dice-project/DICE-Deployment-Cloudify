Apache Spark (standalone)
=========================

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
       type: dice.hosts.ubuntu.${HOST_SIZE_MASTER}
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
       type: dice.hosts.ubuntu.${HOST_SIZE_WORKER}
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

Template variables
------------------

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

  HOST_SIZE_MASTER, HOST_SIZE_WORKER
    Sizes of the master and worker virtual machines. Available values are
    *Small*, *Medium* and *Large*.
