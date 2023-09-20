#!/bin/bash

if [ -z "$SERVER_DIR" ]
then
    current_cwd=$(pwd)
    export SERVER_DIR="$current_cwd"
fi

# Define the target command
WATCH_CMD="python3 $SERVER_DIR/logwatch_json.py"
MODEL_CMD="text-generation-launcher"
AUTH_CMD="$SERVER_DIR/auth_server_hf_tgi.py" 


# Get the process IDs (PIDs) of processes matching the target command
PIDS1=$(ps aux | grep "$WATCH_CMD" | grep -v grep | awk '{print $2}')
PIDS2=$(ps aux | grep "$MODEL_CMD" | grep -v grep | awk '{print $2}')
PIDS4=$(ps aux | grep "$AUTH_CMD" | grep -v grep | awk '{print $2}')

# Check if any processes were found
while ! ([ -z "$PIDS1" ] && [ -z "$PIDS2" ] && [ -z "$PIDS3" ] && [ -z "$PIDS4" ])
do
  # Loop through the PIDs and kill each process
  for PID in $PIDS1; do
    echo "Killing process $PID running: $WATCH_CMD"
    kill "$PID"
  done
  for PID in $PIDS2; do
    echo "Killing process $PID running: $MODEL_CMD"
    kill "$PID"
  done
  for PID in $PIDS4; do
    echo "Killing process $PID running: $AUTH_CMD"
    kill "$PID"
  done
  sleep 2
  PIDS1=$(ps aux | grep "$WATCH_CMD" | grep -v grep | awk '{print $2}')
  PIDS2=$(ps aux | grep "$MODEL_CMD" | grep -v grep | awk '{print $2}')
  PIDS4=$(ps aux | grep "$AUTH_CMD" | grep -v grep | awk '{print $2}')
done

if [ -e "$SERVER_DIR/infer.log" ]
then
  rm "$SERVER_DIR/infer.log"
fi