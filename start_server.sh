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
    git clone -b init_check https://github.com/vast-ai/vast-pyworker
    touch ~/.no_auto_tmux
    touch /root/hasbooted
fi
cd /home/workspace/vast-pyworker

export SERVER_DIR="/home/workspace/vast-pyworker"
export PATH="/opt/conda/bin:$PATH"
export REPORT_ADDR="https://run.vast.ai"

if [ -z "$REPORT_ADDR" ] || [ -z "$MODEL_CMD" ] || [ -z "$AUTH_PORT" ]; then
  echo "REPORT_ADDR, MODEL_CMD, AUTH_PORT env variables must be set!"
  #example: https://idea-catalogue-cleaner-lg.trycloudflare.com meta-llama/Llama-2-70b-chat-hf 3000
  exit 1
fi

source "$SERVER_DIR/start_auth.sh"
source "$SERVER_DIR/start_watch.sh"
source "$SERVER_DIR/launch_model.sh"

sleep 1
source "$SERVER_DIR/init_check.sh"

if [ $? -eq 0 ]; then
    echo "init_check passed, all server function operating correctly."
else
    echo "init_check failed. Exit code: $?"
fi
