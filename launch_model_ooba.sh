
MODEL_NAME=TheBloke/Llama-2-13B-chat-GPTQ
/scripts/docker-entrypoint.sh python3 /app/download-model.py $MODEL_NAME
python3 /app/server.py --extensions api --model $MODEL_NAME --listen