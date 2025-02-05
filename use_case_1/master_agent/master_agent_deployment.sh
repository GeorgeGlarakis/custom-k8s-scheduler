#!/bin/bash

MASTER=$(kubectl get nodes -l role=master -o jsonpath='{.items[*].metadata.name}')
JOB_CREATION_TIME_MIN=500
JOB_CREATION_TIME_MAX=1000
CPU_SPEED_DEVIDER=1
GET_CODE_NETWORK_SPEED=1
GET_DATA_NETWORK_SPEED=1000

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $MASTER-master-agent-deployment
  labels:
    app: $MASTER-master-agent
    redis_host: $MASTER-master-redis 
spec:
  selector:
    matchLabels:
      app: $MASTER-master-agent
      role: code
  replicas: 1
  template:
    metadata:
      labels:
        app: $MASTER-master-agent
        role: code
    spec:
      serviceAccountName: $SERVICE_ACCOUNT_NAME
      containers:
      - name:  $MASTER-master-agent-pod
        image: docker.io/glarakis99/master_code:latest
        env:
        - name: NODE_NAME
          value: $MASTER
        - name: SCHEDULER_NAME
          value: $SCHEDULER_NAME
        - name: JOB_CREATION_TIME_MIN
          value: "$JOB_CREATION_TIME_MIN"
        - name: JOB_CREATION_TIME_MAX
          value: "$JOB_CREATION_TIME_MAX"
        - name: CPU_SPEED_DEVIDER
          value: "$CPU_SPEED_DEVIDER"
        - name: GET_CODE_NETWORK_SPEED
          value: "$GET_CODE_NETWORK_SPEED"
        - name: GET_DATA_NETWORK_SPEED
          value: "$GET_DATA_NETWORK_SPEED"
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
apiVersion: v1
kind: Service
metadata:
  name: $MASTER-master-agent-service
  labels:
    app: $MASTER-master-agent
spec:
  selector:
    app: $MASTER-master-agent
    role: code
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
  clusterIP: None
  type: ClusterIP

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $MASTER-master-redis-deployment
  labels:
    app: $MASTER-master-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $MASTER-master-redis
      role: data
  template:
    metadata:
      labels:
        app: $MASTER-master-redis
        role: data
    spec:
      containers:
      - name: $MASTER-master-redis
        image: redis/redis-stack-server:7.4.0-v1
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
  name: $MASTER-master-redis-service
  labels:
    app: redis
spec:
  selector:
    app: $MASTER-master-redis
    role: data
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
  clusterIP: None
  type: ClusterIP

EOF