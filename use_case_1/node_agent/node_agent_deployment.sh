#!/bin/bash

# NODES=$(kubectl get nodes -l role=worker -o jsonpath='{.items[*].metadata.name}')
NODES=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')
PV_MOUNT_PATH="/mnt/data"

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

# ---
# apiVersion: v1
# kind: PersistentVolume
# metadata:
#   name: $NODE-pv
# spec:
#   capacity:
#     storage: 1Gi
#   accessModes:
#     - ReadWriteMany
#   persistentVolumeReclaimPolicy: Delete
#   storageClassName: local-storage
#   hostPath:
#     path: $PV_MOUNT_PATH
#   nodeAffinity:
#     required:
#       nodeSelectorTerms:
#         - matchExpressions:
#             - key: kubernetes.io/hostname
#               operator: In
#               values:
#                 - $NODE

# ---
# apiVersion: v1
# kind: PersistentVolumeClaim
# metadata:
#   name: $NODE-pvc
# spec:
#   storageClassName: local-storage
#   accessModes:
#     - ReadWriteMany
#   resources:
#     requests:
#       storage: 1Gi
#   volumeName: $NODE-pv

EOF
done

# NODE=node
# cat <<EOF | kubectl apply -f -
# apiVersion: v1
# kind: PersistentVolume
# metadata:
#   name: $NODE-pv
# spec:
#   capacity:
#     storage: 1Gi
#   accessModes:
#     - ReadWriteMany
#   persistentVolumeReclaimPolicy: Delete
#   storageClassName: local-storage
#   hostPath:
#     path: $PV_MOUNT_PATH
#   nodeAffinity:
#     required:
#       nodeSelectorTerms:
#         - matchExpressions:
#             - key: kubernetes.io/hostname
#               operator: In
#               values:
#                 - $NODE

# ---
# apiVersion: v1
# kind: PersistentVolumeClaim
# metadata:
#   name: $NODE-pvc
# spec:
#   storageClassName: local-storage
#   accessModes:
#     - ReadWriteMany
#   resources:
#     requests:
#       storage: 1Gi
#   volumeName: $NODE-pv

# EOF