#!/bin/bash

DATA_ID=data-1
PV_MOUNT_PATH="/mnt/data"
NODE=node-m02

cat <<EOF | kubectl apply -f -
# cat <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-deployment
  labels:
    app: $DATA_ID
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $DATA_ID
      role: data
  template:
    metadata:
      labels:
        app: $DATA_ID
        role: data
        code_id: code-1
    spec:    
      containers:
      - name: data-pod
        image: redis:7.4-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "256Mi"
            cpu: "500m"
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
  name: $DATA_ID
  labels:
    app: $DATA_ID
spec:
  selector:
    app: $DATA_ID
    role: data
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
  clusterIP: None  # Headless service, if you want direct pod access
  type: ClusterIP  # Internal access only

EOF