#!/bin/bash
echo "onstart_TGI_test_nick.sh"
date;
env | grep _ >> /etc/environment;

if [ ! -f /root/hasbooted ]
then
    pip install flask
    pip install nltk
    pip install pycryptodome
    mkdir /home/workspace
    cd /home/workspace
    git clone -b handle-error-test https://github.com/vast-ai/vast-pyworker
    touch ~/.no_auto_tmux
    touch /root/hasbooted
fi
cd /home/workspace/vast-pyworker

export SERVER_DIR="/home/workspace/vast-pyworker"
export PATH="/opt/conda/bin:$PATH"
export REPORT_ADDR="https://tc-celtic-overview-cons.trycloudflare.com"

if [ -z "$REPORT_ADDR" ] || [ -z "$MODEL_CMD" ] || [ -z "$AUTH_PORT" ]; then
  echo "REPORT_ADDR, MODEL_CMD, AUTH_PORT env variables must be set!"
  #example: https://idea-catalogue-cleaner-lg.trycloudflare.com meta-llama/Llama-2-70b-chat-hf 3000
  exit 1
fi

source "$SERVER_DIR/start_auth.sh"
source "$SERVER_DIR/start_watch.sh"
source "$SERVER_DIR/launch_model.sh"