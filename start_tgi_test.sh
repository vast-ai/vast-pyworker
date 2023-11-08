export BACKEND=tgi 
export MODEL_ARGS="--model-id TheBloke/Llama-2-7B-Chat-GPTQ --quantize gptq" 
wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/main/start_server.sh | bash