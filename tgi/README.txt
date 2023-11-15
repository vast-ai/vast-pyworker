Environment variables to set (change to your values):

-e MODEL_ARGS="--model-id TheBloke/Llama-2-70B-chat-GPTQ --quantize gptq"

You can see all possible model arguments here: https://github.com/huggingface/text-generation-inference/blob/main/launcher/src/main.rs#L122.

-e HUGGING_FACE_HUB_TOKEN=””

If you are trying to download a gated model from huggingface, you need to specify your access token. More information on these access tokens can be found here: https://huggingface.co/docs/hub/security-tokens

Full "launch_args" for Autogroup (note that --disk with depend on your model size):

"--image ghcr.io/huggingface/text-generation-inference:1.0.3 --env '-p 3000:3000' --onstart-cmd 'wget -O - https://raw.githubusercontent.com/vast-ai/vast-pyworker/helloautoscaler-local/scripts/launch_tgi.sh | bash' --disk 8.0 --ssh --direct"


