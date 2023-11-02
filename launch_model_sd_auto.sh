curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
sudo apt install git-lfs
git lfs install
cd /home/workspace
git clone https://$HF_USERNAME:$HUGGING_FACE_HUB_TOKEN@huggingface.co/$HF_MODEL_USER/$HF_MODEL_REPO

python /stable-diffusion-webui/launch.py --api-log --nowebui --ckpt /home/workspace/$HF_MODEL_REPO/$HF_MODEL_FILE --port 5000 > $SERVER_DIR/infer.log 2>&1 &
echo "launched model"