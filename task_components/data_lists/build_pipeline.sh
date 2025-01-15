#!/bin/bash

docker build -t "glarakis99/init-data" .
docker push "glarakis99/init-data:latest"

NODE_NAME=master

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
      restartPolicy: Never

EOF