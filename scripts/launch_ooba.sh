#!/bin/bash
echo "launch_ooba.sh" | tee -a /root/debug.log

SERVER_DIR="/home/workspace/vast-pyworker"

start_server() {
    if [ ! -d "$1" ]
    then
        wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/helloautoscaler-test/start_server.sh | bash -s "$2"
    else
        $1/start_server.sh "$2"
    fi
}

start_server "$SERVER_DIR" "ooba"
deactivate

if [ ! -f "/home/workspace/init_launch" ]
then
    pip install accelerate -U
    pip install protobuf
    python -m pip install git+https://github.com/jllllll/exllama
    touch /home/workspace/init_launch
fi

if [ -z "$MODEL_USER" ] || [ -z "$MODEL_NAME" ]
then
    MODEL_USER=TheBloke
    MODEL_NAME=Llama-2-13B-chat-GPTQ
fi

MODEL_PATH="models/${MODEL_USER}_${MODEL_NAME}"
echo "$MODEL_PATH"
cd /src
if [ ! -d "$MODEL_PATH" ]
then
    echo "starting model download" > $SERVER_DIR/infer.log
    python3 /app/download-model.py $MODEL_USER/$MODEL_NAME > $SERVER_DIR/download.log 2>&1
fi
python3 /app/server.py --extensions api --api-blocking-port 5001 --api-streaming-port 5002 --model $MODEL_PATH --listen >> $SERVER_DIR/infer.log 2>&1 &
echo "done"