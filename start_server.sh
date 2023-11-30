#!/bin/bash
echo "start_server.sh" | tee -a /root/debug.log
date;
env | grep _ >> /etc/environment;

export BACKEND=$1
# export REPORT_ADDR="https://holder-suffered-regarding-hansen.trycloudflare.com"

if [ -z "$BACKEND" ]; then
  echo "BACKEND must be set!"
  exit 1
fi

echo "$BACKEND" | tee -a /root/debug.log

if [ ! -f /root/hasbooted2 ]
then
    echo "booting" | tee -a /root/debug.log
    mkdir /home/workspace
    cd /home/workspace
    git clone -b autoscaler-test-2 https://github.com/vast-ai/vast-pyworker

    if [ ! -d "/home/workspace/worker-env" ]
    then
        python3 -m venv /home/workspace/worker-env
    fi

    source /home/workspace/worker-env/bin/activate

    pip install requests
    pip install psutil
    pip install flask
    pip install nltk
    pip install pycryptodome
    pip install numpy

    touch ~/.no_auto_tmux
    touch /root/hasbooted2
fi

if [ "$VIRTUAL_ENV" != "/home/workspace/worker-env" ]
then
    source /home/workspace/worker-env/bin/activate
    echo "environment activated" | tee -a /root/debug.log
fi
echo "venv: $VIRTUAL_ENV" | tee -a /root/debug.log

cd /home/workspace/vast-pyworker
export SERVER_DIR="/home/workspace/vast-pyworker"

if [ -z "$REPORT_ADDR" ]
then
    export REPORT_ADDR="https://run.vast.ai"
fi

if [ -z "$MASTER_TOKEN" ]
then
    export MASTER_TOKEN="mtoken"
fi

export AUTH_PORT=3000

if [ ! -d "$SERVER_DIR/$BACKEND" ]
then
    echo "$BACKEND not supported!" | tee -a /root/debug.log
    exit 1
fi

source "$SERVER_DIR/start_auth.sh"
source "$SERVER_DIR/start_watch.sh"

echo "start server done" | tee -a /root/debug.log

# sleep 1
# source "$SERVER_DIR/init_check.sh"

# if [ $? -eq 0 ]; then
#     echo "init_check passed, all server functions operating correctly."
# else
#     echo "init_check failed. Exit code: $?"
# fi
