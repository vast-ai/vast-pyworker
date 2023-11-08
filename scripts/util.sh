start_server() {
    if [ ! -d "$1" ]
    then
        wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/main/start_server.sh | bash -s $2
    else
        $1/start_server.sh $2
    fi
}