#!/bin/bash

set -e
echo "Starting data initialization..."
redis-cli

JSON.SET data:1 . '{"id": 1, "list": [1, 2, 3, 4, 5]}'
JSON.SET data:2 . '{"id": 2, "list": [6, 7, 8, 9, 10]}'
JSON.SET data:3 . '{"id": 3, "list": [11, 12, 13, 14, 15]}'
JSON.SET data:4 . '{"id": 4, "list": [16, 17, 18, 19, 20]}'