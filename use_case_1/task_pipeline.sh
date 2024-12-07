#!/bin/bash

export SCHEDULER_NAME=my-scheduler
export NODE_NAME=node-m02

cd /home/glarakis/ceid_thesis/custom-k8s-scheduler

kubectl delete job code-job

chmod +x ./use_case_1/dummy_task/code/code_deployment.sh
./use_case_1/dummy_task/code/code_deployment.sh