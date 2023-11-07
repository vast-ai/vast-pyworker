#!/bin/bash

deactivate #deactivates the vast-pyworker venv, in preperation for activating the backend specific venv
if [ ! -f "/home/workspace/init_launch" ]
then
    rsync --remove-source-files -rlptDu --ignore-existing /venv/ /workspace/venv/
    if [ -n "$HF_MODEL_REPO" ]
    then
        curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
        sudo apt install git-lfs
        git lfs install
        cd /home/workspace
        echo "starting model download" > $SERVER_DIR/infer.log
        git clone https://$HF_USERNAME:$HUGGING_FACE_HUB_TOKEN@huggingface.co/$HF_MODEL_USER/$HF_MODEL_REPO
    fi
    touch /home/workspace/init_launch
fi

source /workspace/venv/bin/activate

if [ -n "$HF_MODEL_REPO" ]
then
    CKPT_ARG="--ckpt /home/workspace/$HF_MODEL_REPO/$HF_MODEL_FILE"
else
    CKPT_ARG=""
fi
python /stable-diffusion-webui/launch.py $CKPT_ARG $MODEL_ARGS --api-log --nowebui --port 5000 >> $SERVER_DIR/infer.log 2>&1 &
echo "launched model"