#!/bin/bash

set -e
echo "Starting prune images..."

crictl rmi --prune