Source: https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/

`docker build -t glarakis99/custom-k8s-scheduler:sample .`
`docker push glarakis99/custom-k8s-scheduler:sample`

`kubectl create -f my-scheduler.yaml`
`kubectl get pods --namespace=kube-system`

`kubectl edit clusterrole system:kube-scheduler`