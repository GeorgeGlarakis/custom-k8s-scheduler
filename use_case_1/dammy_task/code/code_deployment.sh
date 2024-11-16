#!/bin/bash

cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: code-job
  labels:
    app: code-1
spec:
  template:
    metadata:
      labels:
        app: code-1
        role: code
        complexity: simple
        data_id: data-1
    spec:
      schedulerName: $SCHEDULER_NAME
      containers:
      - name:  code-pod
        image: docker.io/glarakis99/code_pod:latest
        env:
        - name: LOG_LEVEL
          value: $LOG_LEVEL
        - name: DATA_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['data_id']
        - name: NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
      restartPolicy: Never

EOF

# Add PodAffinity