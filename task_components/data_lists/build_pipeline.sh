#!/bin/bash

docker build -t "glarakis99/init-data" .
docker push "glarakis99/init-data:latest"

NODE_NAME=node
LIST_COUNT=10
LIST_STEP=10000 # < 10000
FUNCTION=same # scale | same

cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: init-data
  labels:
    app: data
spec:
  template:
    metadata:
      labels:
        app: data
        role: data
    spec:
      containers:
      - name:  init-data
        image: docker.io/glarakis99/init-data:latest
        env:
        - name: NODE_NAME
          value: $NODE_NAME
        - name: LIST_COUNT
          value: "$LIST_COUNT"
        - name: LIST_STEP
          value: "$LIST_STEP"
        - name: FUNCTION
          value: $FUNCTION
      restartPolicy: Never

EOF