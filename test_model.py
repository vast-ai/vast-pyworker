import json
import os

def find_tgi_model_path(author_name, model_name):
    models_dir = f"models--{author_name}--{model_name}"
    models_dir_path = f"/data/{models_dir}"
    if os.path.exists(models_dir_path):
        snapshots = os.listdir(f"{models_dir_path}/snapshots")
        snapshot = snapshots[0]
        return f"{models_dir_path}/snapshots/{snapshot}"
    else:
        return None
        
def load_tokens(model_dir):
    tokens_path = f"{model_dir}/tokenizer.model"
    with open(tokens_path, "r") as file:
        print(file.readlines(1))

    # return token_dict["model"]["vocab"]

def make_random_prompt(prompt_len):
    pass


def main():
    model_dir = find_tgi_model_path("TheBloke", "Llama-2-70B-chat-GPTQ")
    print(model_dir)
    vocab = load_tokens(model_dir)
    # print(len(vocab))

if __name__ == "__main__":
    main()