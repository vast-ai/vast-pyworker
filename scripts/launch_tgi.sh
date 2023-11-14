#!/bin/bash
echo "launch_tgi.sh" | tee -a /root/debug.log

SERVER_DIR=/home/workspace/vast-pyworker
export REPORT_ADDR="https://matt-laos-labour-outlined.trycloudflare.com"

start_server() {
    if [ ! -d "$1" ]
    then
        wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/helloautoscaler-local/start_server.sh | bash -s "$2"
    else
        $1/start_server.sh "$2"
    fi
}

start_server "$SERVER_DIR" "tgi"

if [ -z "$MODEL_ARGS" ]
then
    if [ ! -z "$MODEL_CMD" ]
    then
        MODEL_ARGS="$MODEL_CMD"  
    else
        MODEL_ARGS="--model-id TheBloke/Llama-2-7B-chat-GPTQ --quantize gptq"
    fi
fi

echo "using args: $MODEL_ARGS" | tee -a /root/debug.log

MODEL_LAUNCH_CMD="text-generation-launcher"
MODEL_PID=$(ps aux | grep "$MODEL_LAUNCH_CMD" | grep -v grep | awk '{print $2}')

if [ -z "$MODEL_PID" ]
then
    echo "starting model download" > $SERVER_DIR/infer.log
    text-generation-launcher $MODEL_ARGS --json-output --port 5001 --hostname "127.0.0.1" &>> $SERVER_DIR/infer.log  &
    echo "launched model" | tee -a /root/debug.log
else
    echo "model already running" | tee -a /root/debug.log
fi

