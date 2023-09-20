#!/bin/bash
env | grep _ >> /etc/environment;
if [ ! -f /root/hasbooted ]
then
    pip install flask
    mkdir /home/workspace
    cd /home/workspace
    git clone https://github.com/vast-ai/vast-pyworker;
    touch ~/.no_auto_tmux
    touch /root/hasbooted
fi
cd /home/workspace/vast-pyworker

export SERVER_DIR="/home/workspace/vast-pyworker"
export PATH="/opt/conda/bin:$PATH"
export REPORT_ADDR="" #needs to be changed manually in the version at the path https://s3.amazonaws.com/vast.ai/start_server.sh

if ! ([-z "$REPORT_ADDR" ] && [-z "$MODEL_CMD" ] && [-z "$AUTH_PORT" ])
then
  echo "REPORT_ADDR, MODEL_CMD, AUTH_PORT env variables must be set!"
  #example: https://idea-catalogue-cleaner-lg.trycloudflare.com "--model-id meta-llama/Llama-2-70b-chat-hf --json-output --port 5001 --hostname \"127.0.0.1\"" 3000
  exit 1
fi

source "$SERVER_DIR/start_auth.sh"
sleep 3
source "$SERVER_DIR/start_watch.sh"
source "$SERVER_DIR/launch_model.sh"
