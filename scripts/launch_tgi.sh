#!/bin/bash
SERVER_DIR=/home/workspace/vast-pyworker
start_server() {
    if [ ! -d "$1" ]
    then
        wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/helloautoscaler/start_server.sh | bash -s $2
    else
        $1/start_server.sh $2
    fi
}

start_server $SERVER_DIR tgi |& tee /root/debug.log

echo "resuming launch_tgi"

if [ -z "$MODEL_ARGS" ]
then
    if [ ! -z "$MODEL_CMD" ]
    then
        MODEL_ARGS="$MODEL_CMD"  
    else
        MODEL_ARGS="--model-id TheBloke/Llama-2-7B-chat-GPTQ --quantize gptq"
    fi
fi

echo "using args: $MODEL_ARGS" | tee /root/debug.log

MODEL_LAUNCH_CMD="text-generation-launcher"
MODEL_PID=$(ps aux | grep "$MODEL_LAUNCH_CMD" | grep -v grep | awk '{print $2}')

if [ -z "$MODEL_PID" ]
then
    echo "starting model download" |& tee $SERVER_DIR/infer.log /root/debug.log
    text-generation-launcher $MODEL_ARGS --json-output --port 5001 --hostname "127.0.0.1" |& tee $SERVER_DIR/infer.log /root/debug.log &
    echo "launched model" | tee /root/debug.log
else
    echo "model already running" | tee /root/debug.log
fi

echo "launch_tgi done"
