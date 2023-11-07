#!/bin/bash

if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
fi

MODEL_LAUNCH_CMD="text-generation-launcher"
MODEL_PID=$(ps aux | grep "$MODEL_LAUNCH_CMD" | grep -v grep | awk '{print $2}')

echo "using args: $MODEL_ARGS"

if [ ! -f "/home/workspace/init_launch" ]
then
    pip install optimum
    pip install auto-gptq
    touch /home/workspace/init_launch
fi

if [ -z "$MODEL_PID" ]
then
    echo "starting model download" > $SERVER_DIR/infer.log
    text-generation-launcher $MODEL_ARGS --json-output --port 5001 --hostname "127.0.0.1" >> $SERVER_DIR/infer.log 2>>&1 &
    echo "launched model"
else
    echo "model already running"
fi
