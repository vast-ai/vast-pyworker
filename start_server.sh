#!/bin/bash
echo "onstart_TGI_test_nick.sh"
date;
env | grep _ >> /etc/environment;

if [ ! -f /root/hasbooted ]
then
    if [ $BACKEND == "TGI" ]; then
        pip install flask
        pip install nltk
        pip install pycryptodome
    elif [ $BACKEND == "OOBA" ]; then
        pip install flask
        pip install nltk
        pip install pycryptodome
        pip install accelerate -U
        pip install protobuf
        python -m pip install git+https://github.com/jllllll/exllama
    fi
    mkdir /home/workspace
    cd /home/workspace
    git clone -b ooba-compat https://github.com/vast-ai/vast-pyworker
    touch ~/.no_auto_tmux
    touch /root/hasbooted
fi
cd /home/workspace/vast-pyworker

export SERVER_DIR="/home/workspace/vast-pyworker"
export PATH="/opt/conda/bin:$PATH"
# export REPORT_ADDR="https://run.vast.ai"
# export BACKEND="TGI"

if [ -z "$REPORT_ADDR" ] || [ -z "$BACKEND" ] || [ -z "$AUTH_PORT" ]; then
  echo "REPORT_ADDR, BACKEND, AUTH_PORT env variables must be set!"
  exit 1
fi

if [ $BACKEND == "TGI" ]; then
    export WATCH_CMD="python3 $SERVER_DIR/logwatch_json.py"
elif [ $BACKEND == "OOBA" ]; then
    export WATCH_CMD="python3 $SERVER_DIR/logwatch_ooba.py"
else
    echo "Invalid Backend: $BACKEND"
    exit 1
fi

source "$SERVER_DIR/start_auth.sh"
source "$SERVER_DIR/start_watch.sh"
if [ $BACKEND == "TGI" ]; then
    source "$SERVER_DIR/launch_model.sh"
elif [ $BACKEND == "OOBA" ]; then
    source "$SERVER_DIR/launch_model_ooba.sh"
else
    echo "Invalid Backend: $BACKEND"
    exit 1
fi

# sleep 1
# source "$SERVER_DIR/init_check.sh"

# if [ $? -eq 0 ]; then
#     echo "init_check passed, all server functions operating correctly."
# else
#     echo "init_check failed. Exit code: $?"
# fi
