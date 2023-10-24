#!/bin/bash

if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
fi

ACCOUNT_NAME=TheBloke
MODEL_NAME=Llama-2-13B-chat-GPTQ
export MODEL_PATH="models/${ACCOUNT_NAME}_${MODEL_NAME}"
echo "$MODEL_PATH"
cd /src
python3 /app/download-model.py $ACCOUNT_NAME/$MODEL_NAME > $SERVER_DIR/download.log 2>&1
python3 /app/server.py --extensions api --api-blocking-port 5001 --model $MODEL_PATH --listen > $SERVER_DIR/infer.log 2>&1 &
echo "done"