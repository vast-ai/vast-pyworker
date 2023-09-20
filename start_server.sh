#!/bin/bash

export SERVER_DIR="/home/workspace/host-server"
export PATH="/opt/conda/bin:$PATH"

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 REPORT_ADDR MODEL_NAME AUTH_PORT"
  #example: ./start_server.sh https://idea-catalogue-cleaner-lg.trycloudflare.com meta-llama/Llama-2-70b-chat-hf 3000
  exit 1
fi

export REPORT_ADDR=$1
echo $REPORT_ADDR
export MODEL_NAME=$2
echo $MODEL_NAME
export AUTH_PORT=$3
echo $AUTH_PORT

source "$SERVER_DIR/start_auth.sh"
sleep 3
source "$SERVER_DIR/start_watch.sh"
source "$SERVER_DIR/launch_model.sh"
