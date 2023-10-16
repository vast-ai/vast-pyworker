packages=("flask" "nltk" "pycryptodome" "requests" "numpy")

for pkg in "${packages[@]}"; do
    if dpkg -l | grep -q "$pkg"; then
        curl -X POST -d "{'error_msg' : 'package failed installing'}" $REPORT_ADDR
        exit 1

# Define the target command
WATCH_CMD="python3 $SERVER_DIR/logwatch_json.py"
MODEL_LAUNCH_CMD="text-generation-launcher"
AUTH_CMD="$SERVER_DIR/tgi_server.py" 

# Get the process IDs (PIDs) of processes matching the target command
PIDS1=$(ps aux | grep "$WATCH_CMD" | grep -v grep | awk '{print $2}')
PIDS2=$(ps aux | grep "$MODEL_LAUNCH_CMD" | grep -v grep | awk '{print $2}')
PIDS3=$(ps aux | grep "$AUTH_CMD" | grep -v grep | awk '{print $2}')

if ([ -z "$PIDS1" ] || [ -z "$PIDS2" ] || [ -z "$PIDS3" ])
do 
    curl -X POST -d "{'error_msg' : 'not all server component processes are running'}" $REPORT_ADDR
    exit 1

