#!/bin/bash

export SERVER_DIR="/home/workspace/host-server"
export PATH="/opt/conda/bin:$PATH"

if ! ([-z "$REPORT_ADDR" ] && [-z "$MODEL_NAME" ] && [-z "$AUTH_PORT" ])
then
  echo "REPORT_ADDR, MODEL_NAME, AUTH_PORT env variables must be set!"
  #example: https://idea-catalogue-cleaner-lg.trycloudflare.com meta-llama/Llama-2-70b-chat-hf 3000
  exit 1
fi

source "$SERVER_DIR/start_auth.sh"
sleep 3
source "$SERVER_DIR/start_watch.sh"
source "$SERVER_DIR/launch_model.sh"
