#!/bin/bash

# NODES=$(kubectl get nodes -l role=worker -o jsonpath='{.items[*].metadata.name}')
NODES=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')
LOG_LEVEL="DEBUG"

for NODE in $NODES; do
  cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $NODE-worker-agent-deployment
  labels:
    app: $NODE-worker-agent
    redis_host: $NODE-worker-redis 
spec:
  selector:
    matchLabels:
      app: $NODE-worker-agent
      role: code
  replicas: 1
  template:
    metadata:
      labels:
        app: $NODE-worker-agent
        role: code
    spec:
      serviceAccountName: sa-scheduler
      containers:
      - name: $NODE-worker-agent-pod
        image: docker.io/glarakis99/node_code:latest
        env:
        - name: NODE_NAME
          value: $NODE
        - name: LOG_LEVEL
          value: $LOG_LEVEL
        imagePullPolicy: Always
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                - $NODE

---
apiVersion: v1
kind: Service
metadata:
  name: $NODE-worker-agent-service
  labels:
    app: $NODE-worker-agent
spec:
  selector:
    app: $NODE-worker-agent
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
  name: $NODE-worker-redis-deployment
  labels:
    app: $NODE-worker-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $NODE-worker-redis
      role: data
  template:
    metadata:
      labels:
        app: $NODE-worker-redis
        role: data
    spec:
      containers:
      - name: $NODE-worker-redis
        image: redis/redis-stack-server:7.4.0-v1
        ports:
        - containerPort: 6379
        env:
        - name: NODE_NAME
          value: $NODE
        - name: LOG_LEVEL
          value: $LOG_LEVEL
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                - $NODE

---
apiVersion: v1
kind: Service
metadata:
  name: $NODE-worker-redis-service
  labels:
    app: $NODE-worker-redis
spec:
  selector:
    app: $NODE-worker-redis
    role: data
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
  clusterIP: None
  type: ClusterIP

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $NODE-task-runner-deployment
  labels:
    app: $NODE-task-runner
    redis_host: $NODE-worker-redis
spec:
  selector:
    matchLabels:
      app: $NODE-task-runner
      role: code
  replicas: 1
  template:
    metadata:
      labels:
        app: $NODE-task-runner
        role: code
    spec:
      serviceAccountName: sa-scheduler
      containers:
      - name: $NODE-task-runner-pod
        image: docker.io/glarakis99/node_task_runner:latest
        env:
        - name: NODE_NAME
          value: $NODE
        - name: LOG_LEVEL
          value: $LOG_LEVEL
        imagePullPolicy: Always
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                - $NODE

EOF
done