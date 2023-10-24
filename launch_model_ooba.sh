#!/bin/bash

if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
fi
export HF_TOKEN=""

# ACCOUNT_NAME=TheBloke
# ACCOUNT_NAME=meta-llama
ACCOUNT_NAME=facebook
# MODEL_NAME=Llama-2-13B-chat-GPTQ
# MODEL_NAME=Llama-2-7b-chat-hf
MODEL_NAME=galactica-125m
/scripts/docker-entrypoint.sh python3 /app/download-model.py $ACCOUNT_NAME/$MODEL_NAME
export MODEL_PATH="models/${ACCOUNT_NAME}_${MODEL_NAME}"
echo "$MODEL_PATH"
python3 /app/server.py --extensions api --model $MODEL_PATH --listen > $SERVER_DIR/infer.log 2>&1 &
echo "done"