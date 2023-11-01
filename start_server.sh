#!/bin/bash
echo "onstart_TGI_test_nick.sh"
date;
env | grep _ >> /etc/environment;

if [ ! -f /root/hasbooted ]
then
    if [ $BACKEND == "OOBA" ]; then
        pip install accelerate -U
        pip install protobuf
        python -m pip install git+https://github.com/jllllll/exllama
    elif [$BACKEND == "SD_AUTO"]; then
        source /venv/bin/activate
    fi
    mkdir /home/workspace
    cd /home/workspace
    git clone -b ooba-compat https://github.com/vast-ai/vast-pyworker

    pip install requests
    pip install flask
    pip install nltk
    pip install pycryptodome
    pip install numpy

    touch ~/.no_auto_tmux
    touch /root/hasbooted
fi
cd /home/workspace/vast-pyworker
if [$BACKEND == "SD_AUTO"]; then
    source /venv/bin/activate
fi

export SERVER_DIR="/home/workspace/vast-pyworker"
export PATH="/opt/conda/bin:$PATH"

if [ -z "$REPORT_ADDR" ] || [ -z "$BACKEND" ] || [ -z "$AUTH_PORT" ]; then
  echo "REPORT_ADDR, BACKEND, AUTH_PORT env variables must be set!"
  exit 1
fi

source "$SERVER_DIR/start_auth.sh"
source "$SERVER_DIR/start_watch.sh"
if [ $BACKEND == "TGI" ]; then
    source "$SERVER_DIR/launch_model_tgi.sh"
elif [ $BACKEND == "OOBA" ]; then
    source "$SERVER_DIR/launch_model_ooba.sh"
elif [ $BACKEND == "SD_AUTO" ]; then
    source "$SERVER_DIR/launch_model_sd_auto.sh"
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
