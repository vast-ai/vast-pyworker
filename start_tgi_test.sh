export BACKEND=tgi 
export MODEL_ARGS="--model-id TheBloke/Llama-2-70 B-Chat-GPTQ --quantize gptq" 
wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/main/start_server.sh | bash