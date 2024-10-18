#!/bin/bash

cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: code-job
  labels:
    app: code_1
spec:
  template:
    metadata:
      labels:
        app: code_1
        role: code
        complexity: simple
        data_id: dammy_1
    spec:
      schedulerName: $SCHEDULER_NAME
      containers:
      - name:  code-pod
        image: docker.io/glarakis99/code_pod:latest
        env:
        - name: NODE_NAME
          value: $NODE_NAME
        - name: DATA_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['data_id']
      restartPolicy:

EOF