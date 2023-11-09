start_server() {
    if [ ! -d "$1" ]
    then
        wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/helloautoscaler/start_server.sh | bash -s $2
    else
        $1/start_server.sh $2
    fi
}

if [ ! -f /root/hasbooted ]
then
    echo "hasbooted doesn't exist"
else
    echo "hasbooted does exist"
fi

start_server /home/workspace/vast-pyworker helloautoscaler