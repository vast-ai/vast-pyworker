vast-pyworker’s integration with AUTOMATIC111’s stable-diffusion-webui allows for the automatic installation of any model hosted on huggingface and the setup of the API.
In order to specify which model you want to use, and authenticate your huggingface account, you must set the following environment variables. If you don’t want to download a custom model, you can just remove all of the following environment variables, and the default model will be loaded.

-e HF_MODEL_REPO="stable-diffusion-xl-base-0.9" 

This is the name of the huggingface model repository.

-e HF_MODEL_USER="stabilityai" 

This is the username of the account that the huggingface model repository belongs to. 

-e HF_MODEL_FILE="sd_xl_base_0.9.safetensors" 

This is the file within the model repository that contains the model weights, and the file that the api will use to load the model.

-e HF_USERNAME="" 

This is the name of your personal huggingface account to authenticate the installation of the model.

-e HUGGING_FACE_HUB_TOKEN="" 

This is the access token for installation. More information on these access tokens can be found here: https://huggingface.co/docs/hub/security-tokens. You can generate a new one at any time. 

-e MODEL_ARGS= “”

Different options are shown here: https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Command-Line-Arguments-and-Settings#all-command-line-arguments. The applicable options are likely found under the “PERFORMANCE” category. Be cautious with the options that are selected as we use certain options to set up the server in API mode, and integrate it with the vast-pyworker framework. These arguments will be used in addition to the arguments we use by default, which can be seen here. This variable is optional.
