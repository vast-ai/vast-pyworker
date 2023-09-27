import subprocess
import json

def get_curr_instances():
	result = subprocess.run(["vastai", "show", "instances", "--raw"], capture_output=True)
	instance_info = result.stdout.decode('utf-8')
	if instance_info:
		try:
			curr_instances = json.loads(instance_info)
		except json.decoder.JSONDecodeError:
			curr_instances = None
	else:
		curr_instances = None

	return curr_instances

def get_model_address(instance):
	addr = instance["public_ipaddr"] + ":" + instance["ports"]["3000/tcp"][0]["HostPort"]
	addr = addr.replace('\n', '')
	return addr


