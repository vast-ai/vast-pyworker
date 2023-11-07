#!/bin/bash

deactivate
if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
fi

if [ ! -f "/home/workspace/init_launch" ]
then
    pip install accelerate -U
    pip install protobuf
    python -m pip install git+https://github.com/jllllll/exllama
    touch /home/workspace/init_launch
fi

MODEL_PATH="models/${MODEL_USER}_${MODEL_NAME}"
echo "$MODEL_PATH"
cd /src
if [ ! -d "$MODEL_PATH" ]
then
echo "starting model download" > $SERVER_DIR/infer.log
    python3 /app/download-model.py $MODEL_USER/$MODEL_NAME > $SERVER_DIR/download.log 2>&1
fi
python3 /app/server.py --extensions api --api-blocking-port 5001 --api-streaming-port 5002 --model $MODEL_PATH --listen >> $SERVER_DIR/infer.log 2>>&1 &
echo "done"