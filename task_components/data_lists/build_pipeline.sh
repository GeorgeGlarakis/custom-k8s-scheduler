#!/bin/bash

docker build -t "glarakis99/init-data" .
docker push "glarakis99/init-data:latest"

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
      restartPolicy: Never

EOF