#!/bin/bash
echo "launch_sdauto2.sh" | tee -a /root/debug.log

SERVER_DIR="/home/workspace/vast-pyworker"

start_server() {
    if [ ! -d "$1" ]
    then
        wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/test-refactor/start_server.sh | bash -s "$2"
    else
        $1/start_server.sh "$2"
    fi
}

start_server "$SERVER_DIR" "sdauto"
deactivate #deactivates the vast-pyworker venv, in preperation for activating the backend specific venv

/opt/ai-dock/bin/init.sh;
echo "launched model"