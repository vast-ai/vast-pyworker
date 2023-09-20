#!/bin/bash

if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
fi

MODEL_CMD="text-generation-launcher"
MODEL_PID=$(ps aux | grep "$MODEL_CMD" | grep -v grep | awk '{print $2}')

if [ -z "$MODEL_PID" ]
then
    text-generation-launcher --model-id $MODEL_NAME --json-output --port 5001 --hostname "127.0.0.1" > $SERVER_DIR/infer.log 2>&1 &
    echo "launched model"
else
    echo "model already running"
fi