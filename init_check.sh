packages=("flask" "nltk" "pycryptodome" "requests" "numpy")
FULL_ADDR="$REPORT_ADDR/worker_status/"

for pkg in "${packages[@]}"; do
    if ! pip show "$pkg" &> /dev/null; then
        echo "$pkg is not installed"
        curl -X POST -d "{'error_msg' : 'package failed installing'}" $FULL_ADDR
        return 1
    else
        echo "$pkg is installed"
    fi       
done

# Define the target command
WATCH_CMD="python3 $SERVER_DIR/logwatch_json.py"
MODEL_LAUNCH_CMD="text-generation-launcher"
AUTH_CMD="$SERVER_DIR/tgi_server.py" 

# Get the process IDs (PIDs) of processes matching the target command
PIDS1=$(ps aux | grep "$WATCH_CMD" | grep -v grep | awk '{print $2}')
PIDS2=$(ps aux | grep "$MODEL_LAUNCH_CMD" | grep -v grep | awk '{print $2}')
PIDS3=$(ps aux | grep "$AUTH_CMD" | grep -v grep | awk '{print $2}')

if ([ -z "$PIDS1" ] || [ -z "$PIDS2" ] || [ -z "$PIDS3" ]); then
    echo "not all server component processes are running"
    curl -X POST -d "{'error_msg' : 'not all server component processes are running'}" $FULL_ADDR
    return 1
else
    echo "all component processes are running"
fi