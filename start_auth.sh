#!/bin/bash

if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
fi

AUTH_CMD="$SERVER_DIR/server.py" 
AUTH_PID=$(ps aux | grep "$AUTH_CMD" | grep -v grep | awk '{print $2}')

while ! [ -z "$AUTH_PID" ]
do
    echo "Killing process $AUTH_PID running: $AUTH_CMD"
    kill "$AUTH_PID"
    sleep 2
    AUTH_PID=$(ps aux | grep "$AUTH_CMD" | grep -v grep | awk '{print $2}')
done

python3 $SERVER_DIR/server.py |& tee $SERVER_DIR/auth.log &
echo "started auth server" | tee /root/debug.log