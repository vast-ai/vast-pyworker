Environment variables to set (change to your values):

-e MODEL_USER=”TheBloke” 
-e MODEL_NAME=”Llama-2-13B-chat-GPTQ”


Full "launch_args" example for Autogroup (note that --disk with depend on your model size):

"--image atinoda/text-generation-webui:default-v1.7 --env '-p 3000:3000 -e MODEL_USER=TheBloke -e MODEL_NAME=Llama-2-7B-chat-GPTQ' --onstart wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/main/scripts/launch_ooba.sh | bash --disk 8.0 --ssh"
