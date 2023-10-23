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
    mkdir /home/workspace
    cd /home/workspace
    git clone -b ooba-compat https://github.com/vast-ai/vast-pyworker
    touch ~/.no_auto_tmux
    touch /root/hasbooted
fi
cd /home/workspace/vast-pyworker

export SERVER_DIR="/home/workspace/vast-pyworker"
export PATH="/opt/conda/bin:$PATH"
export REPORT_ADDR="https://run.vast.ai"
export MASTER_TOKEN="mtoken"

source "$SERVER_DIR/start_auth.sh"
source "$SERVER_DIR/launch_model_ooba.sh"