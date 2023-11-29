start_server() {
    if [ ! -d "$1" ]
    then
        wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/autoscaler-test-2/start_server.sh | bash -s "$2"
    else
        $1/start_server.sh "$2"
    fi
}

if [ ! -f "/home/workspace/init_launch" ]
then
    pip install vllm
    touch "/home/workspace/init_launch"
fi

export MODEL_NAME="mistralai/Mistral-7B-v0.1"

start_server "/home/workspace/vast-pyworker" "vllm"