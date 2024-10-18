#!/bin/bash

NODES=$(kubectl get nodes -l role=worker -o jsonpath='{.items[*].metadata.name}')

for NODE in $NODES; do
  cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $NODE-agent-deployment
  labels:
    app: $NODE-agent
    redis_host: $NODE-redis 
spec:
  selector:
    matchLabels:
      app: $NODE-agent
      role: code
  replicas: 1
  template:
    metadata:
      labels:
        app: $NODE-agent
        role: code
    spec:
      serviceAccountName: sa-scheduler
      containers:
      - name: $NODE-agent-pod
        image: docker.io/glarakis99/node_code:latest
        env:
        - name: NODE_NAME
          value: $NODE
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
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $NODE-redis-deployment
  labels:
    app: $NODE-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $NODE-redis
      role: data
  template:
    metadata:
      labels:
        app: $NODE-redis
        role: data
    spec:
      containers:
      - name: $NODE-redis
        image: redis:7.4-alpine
        ports:
        - containerPort: 6379
        env:
        - name: NODE_NAME
          value: $NODE
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
  name: $NODE-redis-service
  labels:
    app: $NODE-redis
spec:
  selector:
    app: $NODE-redis
    role: data
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
  clusterIP: None
  type: ClusterIP
EOF
done