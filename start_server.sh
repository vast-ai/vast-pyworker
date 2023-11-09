#!/bin/bash
echo "start_server.sh"
date;
env | grep _ >> /etc/environment;

export BACKEND=$1

if [ ! -f /root/hasbooted ]
then  
    mkdir /home/workspace
    cd /home/workspace
    git clone -b helloautoscaler https://github.com/vast-ai/vast-pyworker
    
    python3 -m venv /home/workspace/worker-env
    source /home/workspace/worker-env/bin/activate

    pip install requests
    pip install psutil
    pip install flask
    pip install nltk
    pip install pycryptodome
    pip install numpy

    touch ~/.no_auto_tmux
    touch /root/hasbooted
fi

echo "$VIRTUAL_ENV"
if [ "$VIRTUAL_ENV" != "/home/workspace/worker-env" ]
then
    source /home/workspace/worker-env/bin/activate
    echo "environment activated"
fi

cd /home/workspace/vast-pyworker
export SERVER_DIR="/home/workspace/vast-pyworker"
export REPORT_ADDR="https://run.vast.ai"

if [ -z "$MASTER_TOKEN" ]
then
    export MASTER_TOKEN="mtoken"
fi

export AUTH_PORT=3000

if [ -z "$REPORT_ADDR" ] || [ -z "$BACKEND" ] || [ -z "$AUTH_PORT" ]; then
  echo "REPORT_ADDR, BACKEND, AUTH_PORT env variables must be set!"
  exit 1
fi

if [ ! -d "$SERVER_DIR/$BACKEND" ]
then
    echo "$BACKEND not supported!"
    exit 1
fi

source "$SERVER_DIR/start_auth.sh"
source "$SERVER_DIR/start_watch.sh"
if [ -f "$SERVER_DIR/$BACKEND/launch.sh" ]
then
    source "$SERVER_DIR/$BACKEND/launch.sh"
fi

# sleep 1
# source "$SERVER_DIR/init_check.sh"

# if [ $? -eq 0 ]; then
#     echo "init_check passed, all server functions operating correctly."
# else
#     echo "init_check failed. Exit code: $?"
# fi
