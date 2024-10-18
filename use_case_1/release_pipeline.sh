#!/bin/bash
# set -e

(
cd /home/glarakis/ceid_thesis/custom-k8s-scheduler/use_case_1/dammy_task/code
docker build -t glarakis99/code_pod:latest .
docker push glarakis99/code_pod:latest
) &
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

wait

##### ----------------------------------------------------------------------------

kubectl delete deployment node-agent-deployment
kubectl delete deployment node-redis-deployment
kubectl delete deployment node-m02-agent-deployment
kubectl delete deployment node-m02-redis-deployment
kubectl delete deployment code-deployment

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

cd /home/glarakis/ceid_thesis/custom-k8s-scheduler

bash ./service_account.sh
bash ./use_case_1/master_agent/master_agent_deployment.sh
bash ./use_case_1/node_agent/node_agent_deployment.sh
