#!/bin/bash

MASTER=$(kubectl get nodes -l role=master -o jsonpath='{.items[*].metadata.name}')

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $MASTER-agent-deployment
  labels:
    app: $MASTER-agent
    redis_host: $MASTER-redis 
spec:
  selector:
    matchLabels:
      app: $MASTER-agent
      role: code
  replicas: 1
  template:
    metadata:
      labels:
        app: $MASTER-agent
        role: code
    spec:
      serviceAccountName: $SERVICE_ACCOUNT_NAME
      containers:
      - name:  $MASTER-agent-pod
        image: docker.io/glarakis99/master_code:latest
        env:
        - name: NODE_NAME
          value: $MASTER
        - name: SCHEDULER_NAME
          value: $SCHEDULER_NAME
        imagePullPolicy: Always
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: role
                operator: In
                values:
                - master
      

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $MASTER-redis-deployment
  labels:
    app: $MASTER-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $MASTER-redis
      role: data
  template:
    metadata:
      labels:
        app: $MASTER-redis
        role: data
    spec:
      containers:
      - name: $MASTER-redis
        image: redis:7.4-alpine
        ports:
        - containerPort: 6379
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: role
                operator: In
                values:
                - master

---
apiVersion: v1
kind: Service
metadata:
  name: $MASTER-redis-service
  labels:
    app: redis
spec:
  selector:
    app: $MASTER-redis
    role: data
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
  clusterIP: None
  type: ClusterIP

EOF