#!/bin/bash

set -e
echo "Starting migration..."

# SOURCE_NODE=node_x
# DESTINATION_NODE=node_y
# PV_PATH="/mnt/data"
# DATA_DEPLOYMENT_NAME=data_x
# BACKUP_FILE_NAME=dump.rdb
BACKUP_FILE_PATH="$PV_PATH/$DATA_DEPLOYMENT_NAME/$BACKUP_FILE_NAME"

REDIS_SVC_NAME=$DATA_DEPLOYMENT_NAME.$NAMESPACE.svc.cluster.local
# REDIS_PORT=6379

/usr/bin/redis-cli -u redis://default@$REDIS_SVC_NAME:$REDIS_PORT/0 SAVE
if [ -e "/mnt/source/$BACKUP_FILE_NAME" ]; then
  # Copy file from source to destination
  echo "Copying file from source to destination..."
  cp "/mnt/source/$BACKUP_FILE_NAME" "/mnt/destination/."

  python3 edit_data_deployment.py
  echo "Migration for $DATA_DEPLOYMENT_NAME completed."
  rm "/mnt/source/$BACKUP_FILE_NAME"

else
  echo "Back up file not found."
fi