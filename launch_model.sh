#!/bin/bash

if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
fi

MODEL_LAUNCH_CMD="text-generation-launcher"
MODEL_PID=$(ps aux | grep "$MODEL_LAUNCH_CMD" | grep -v grep | awk '{print $2}')

if [ -z "$MODEL_PID" ]
then
    text-generation-launcher $MODEL_CMD > $SERVER_DIR/infer.log 2>&1 &
    echo "launched model"
else
    echo "model already running"
fi