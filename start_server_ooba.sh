#!/bin/bash
echo "start_server.sh"
date;
env | grep _ >> /etc/environment;

if [ ! -f /root/hasbooted ]
then
    pip install flask
    pip install nltk
    pip install pycryptodome
    pip install accelerate -U
    pip install protobuf
    python -m pip install git+https://github.com/jllllll/exllama
    mkdir /home/workspace
    cd /home/workspace
    git clone -b ooba-compat https://github.com/vast-ai/vast-pyworker
    touch ~/.no_auto_tmux
    touch /root/hasbooted
fi
cd /home/workspace/vast-pyworker

export SERVER_DIR="/home/workspace/vast-pyworker"
export PATH="/opt/conda/bin:$PATH"
export REPORT_ADDR="https://falling-vaccine-spokesman-joining.trycloudflare.com"
export MASTER_TOKEN="mtoken"
# export CONTAINER_ID=0
export AUTH_PORT=3000
export BACKEND="OOBA"

source "$SERVER_DIR/start_auth.sh"
source "$SERVER_DIR/start_watch_ooba.sh"
source "$SERVER_DIR/launch_model_ooba.sh"