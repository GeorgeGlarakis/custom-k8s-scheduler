#!/bin/bash
# set -e

(
cd /home/glarakis/ceid_thesis/custom-k8s-scheduler/use_case_1/master_agent
docker build -t glarakis99/master_code:latest .
docker push glarakis99/master_code:latest
) &
(
cd /home/glarakis/ceid_thesis/custom-k8s-scheduler/use_case_1/node_agent
docker build -t glarakis99/node_code:latest .
docker push glarakis99/node_code:latest
) &
(
cd /home/glarakis/ceid_thesis/custom-k8s-scheduler/use_case_1/dammy_task/code
docker build -t glarakis99/code_pod:latest .
docker push glarakis99/code_pod:latest
) &
(
cd /home/glarakis/ceid_thesis/custom-k8s-scheduler/use_case_1/dammy_task/data
docker build -t glarakis99/data_pod:latest .
docker push glarakis99/data_pod:latest
) &
(
cd /home/glarakis/ceid_thesis/custom-k8s-scheduler/use_case_1/migration_agent
docker build -t glarakis99/migration_code:latest .
docker push glarakis99/migration_code:latest
) &

wait

##### ----------------------------------------------------------------------------

DEPLOYMENTS=$(kubectl get deployments -o jsonpath='{.items[*].metadata.name}')
for DEPLOYMENT in $DEPLOYMENTS; do
    kubectl delete deployment "$DEPLOYMENT"
done

JOBS=$(kubectl get jobs -o jsonpath='{.items[*].metadata.name}')
for JOB in $JOBS; do
    kubectl delete job "$JOB"
done

PVS=$(kubectl get pv -o jsonpath='{.items[*].metadata.name}')
for PV in $PVS; do
    kubectl delete pv "$PV"
done

PVCS=$(kubectl get pvc -o jsonpath='{.items[*].metadata.name}')
for PVC in $PVCS; do
    kubectl delete pvc "$PVC"
done

# Kubernetes Init
# kubectl label node <node_name> node-role.kubernetes.io/worker=worker

NODES=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')
for NODE in $NODES; do
    if [ "$NODE" = "node" ]; then
        kubectl label nodes "$NODE" role=master --overwrite
    else
        kubectl label nodes "$NODE" role=worker --overwrite
    fi
done

export SERVICE_ACCOUNT_NAME=sa-scheduler
export SCHEDULER_NAME=my-scheduler
export LOG_LEVEL=DEBUG

cd /home/glarakis/ceid_thesis/custom-k8s-scheduler

bash ./service_account.sh
bash ./use_case_1/master_agent/master_agent_deployment.sh
bash ./use_case_1/node_agent/node_agent_deployment.sh
