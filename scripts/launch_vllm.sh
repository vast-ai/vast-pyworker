start_server() {
    if [ ! -d "$1" ]
    then
        wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/autoscaler-test-2/start_server.sh | bash -s "$2"
    else
        $1/start_server.sh "$2"
    fi
}

start_server "/home/workspace/vast-pyworker" "vllm"