#!/bin/bash

export BACKEND=tgi 
export MODEL_ARGS="--model-id TheBloke/Llama-2-70B-chat-GPTQ --quantize gptq --max-batch-prefill-tokens 32768"

if [ ! -d "/home/workspace/vast-pyworker" ]
then
    wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/new-launch/start_server.sh | bash
fi

if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
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
