import requests
import json
import time
from websockets.sync.client import connect
import json

MSG_END = "$$$"

def send_vllm_request_auth(gpu_server_addr, id_token, text_prompt):
	URI = f'http://{gpu_server_addr}/auth'
	model_dict = {"prompt" : text_prompt}
	request_dict = {"token" : id_token, "model" : model_dict}
	text_result = None
	error = None
	num_tokens = None
	try:
		response = requests.post(URI, json=request_dict)
		if response.status_code == 200:
			try:
				reply = response.json()
				if reply["error"] is None:
					text_result = f"{text_prompt} -> {reply['response']}"
					num_tokens = reply["num_tokens"]
				else:
					error = reply['error']
			except json.JSONDecodeError:
				error = "json"
		else:
			error = f"status code: {response.status_code}"
	except requests.exceptions.ConnectionError as e:
		error = f"connection error: {e}"

	return {"reply" : text_result, "error": error, "num_tokens" : num_tokens, "first_msg_wait" : None}

def send_vllm_request_streaming_auth(gpu_server_addr, id_token, text_prompt):
	response = ""
	first_msg_wait = 0.0
	first = True
	with connect(f"ws://{gpu_server_addr}/") as websocket:
		websocket.send(id_token)
		websocket.send(MSG_END)

		websocket.send(text_prompt)
		websocket.send(MSG_END)

		t1 = time.time()
		for message in websocket:
			if first:
				t2 = time.time()
				first_msg_wait = t2 - t1
				first = False
			response += message
	return {"reply" : response, "error" : None, "num_tokens" : 50, "first_msg_wait" : first_msg_wait}


def send_vllm_request_streaming_test_auth(gpu_server_addr, mtoken):
	response = ""
	try:
		with connect(f"ws://{gpu_server_addr}/") as websocket:
			websocket.send(mtoken)
			websocket.send(MSG_END)
			websocket.send("Hello?")
			websocket.send(MSG_END)
			for message in websocket:
				response += message
	except TimeoutError:
		pass
	
	# print(response)
	if response != "":
		return True
	else:
		return False

def send_tgi_prompt(addr, message, signature, text_prompt, max_new_tokens):
	parameters = {"max_new_tokens" : max_new_tokens}
	request_dict = {"message" : message, "signature" : signature, "inputs" : text_prompt, "parameters" : parameters}
	URI = f'{addr}/generate'
	response = ""
	resp = requests.post(URI, json=request_dict, stream=True)
	error = None
	if resp.status_code == 200:
		response = json.loads(resp.content)["generated_text"]
	else:
		error = resp.status_code

	return {"reply" : response, "error" : error, "num_tokens" : max_new_tokens, "first_msg_wait" : None}

def decode_line(line):
	payload = line.decode("utf-8")

	if payload.startswith("data:"):
		json_payload = json.loads(payload.lstrip("data:").rstrip("/n"))
		return json_payload["token"]["text"]
	else:
		return None

def send_tgi_prompt_streaming(addr, token, text_prompt, max_new_tokens):
	parameters = {"max_new_tokens" : max_new_tokens}
	request_dict = {"token" : token, "inputs" : text_prompt, "parameters" : parameters}
	URI = f'{addr}/generate_stream'
	
	num_tokens = 0
	first_msg_wait = 0.0
	first = True
	response = ""
	t1 = time.time()
	resp = requests.post(URI, json=request_dict, stream=True)
	error = None

	if resp.status_code == 200:
		for line in resp.iter_lines():
			if line == b"\n":
				continue

			if first:
				t2 = time.time()
				first_msg_wait = t2 - t1
				first = False

			line_token = decode_line(line)
			
			if line_token:
				response += line_token
				num_tokens += 1
	else:
		error = resp.status_code

	return {"reply" : response, "error" : error, "num_tokens" : num_tokens, "first_msg_wait" : first_msg_wait}


