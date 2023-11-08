#!/bin/bash

export BACKEND=tgi 
export MODEL_ARGS="--model-id TheBloke/Llama-2-7B-chat-GPTQ --quantize gptq"
export SERVER_DIR=/home/workspace/vast-pyworker

if [ ! -d "$SERVER_DIR" ]
then
    wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/new-launch/start_server.sh | bash
else
    source $SERVER_DIR/start_server.sh
fi

MODEL_LAUNCH_CMD="text-generation-launcher"
MODEL_PID=$(ps aux | grep "$MODEL_LAUNCH_CMD" | grep -v grep | awk '{print $2}')

echo "using args: $MODEL_ARGS"

if [ -z "$MODEL_PID" ]
then
    echo "starting model download" > $SERVER_DIR/infer.log
    text-generation-launcher $MODEL_ARGS --json-output --port 5001 --hostname "127.0.0.1" >> $SERVER_DIR/infer.log 2>&1 &
    echo "launched model"
else
    echo "model already running"
fi
