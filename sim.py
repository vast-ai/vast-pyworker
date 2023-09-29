import random
import time
from threading import Thread, Lock, Event
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import resource
import os
import psutil

from sim_client import Client

MAX_CONCURRENCY = 100
JOIN_TIMEOUT = 5

PROMPTS = [ "Yesterday I woke up and I saw that my dog was missing. This made me think that ",
			"I have been thinking a lot about the question of what the best movie of all time is. There are a lot of different ways to approach this question, but for me the most important factor is how exciting it is. With that in mind, I would say the best movie is: ",
			"I hope that one day humans will be able to live on another planet. This planet is great, but there are many issues with it, and it is not clear how long it will last. Other planets are much harder to live on, so it will be hard for other humans to live on them, but in a worst case scenario it would be great to have the option to live on another planet. I think that in order for humans to be able to live on another planet, the following needs to happen: ",
			"In the realm of possibilities, where ideas take shape and dreams find expression, there exists a tapestry of thoughts that intertwine and weave the fabric of our understanding. From the cosmic dance of stars in the night sky to the gentle rustle of leaves in an ancient forest, the universe unfolds its mysteries before our curious gaze. In this vast expanse, the human spirit embarks on a quest for knowledge, driven by an insatiable thirst to unravel the enigma of existence. As we navigate the corridors of time, we are bound by the threads of history that have shaped civilizations and cultures across continents. From the pyramids of Egypt that stand as sentinel monuments to human ingenuity to the intricate temples of Angkor Wat that speak of devotion carved in stone, the echoes of the past reverberate in the present, reminding us of the enduring legacy of our predecessors. The passage of time has ushered in waves of change, ushering in revolutions that have redefined the course of human progress. The clanking gears of the Industrial Revolution gave rise to a new era of mechanization, propelling society into the modern age. Today, the digital revolution weaves a digital tapestry that connects us in ways previously unimaginable, transcending geographical boundaries and fostering a global village of interconnected minds. Amidst the grandeur of nature and the innovations of technology, the human experience is a mosaic of emotions that paint the canvas of our lives. Love, joy, sorrow, and resilience converge to create a symphony of feelings that accompany us through the journey of existence. It is in the embrace of loved ones, the laughter of friends, and the solace of solitude that we find moments of true meaning. Language, the bridge between minds, empowers us to share thoughts, emotions, and ideas with fellow travelers on this cosmic journey. From the verses of ancient poets to the prose of modern storytellers, words have the power to transcend time and touch the souls of generations. Through the written word, we communicate the collective wisdom of humanity, passing down knowledge from one era to the next. The pursuit of knowledge fuels the fires of curiosity that burn within us. Science unfurls the mysteries of the universe, revealing the intricate dance of particles and the cosmic ballet of galaxies. Artistic expression, in its myriad forms, offers a window into the human imagination, capturing the essence of beauty and complexity that define our world. In this grand tapestry of existence, each thread represents a life, each moment a fleeting brushstroke on the canvas of eternity. As we tread the paths of our own narratives, we contribute to the evolving story of humanity, leaving footprints that echo in the corridors of time. The interplay of individual lives and collective destinies weaves a narrative that transcends generations, serving as a testament to the indomitable spirit of the human journey."
]

class User:
	def __init__(self, id, prompt=PROMPTS[0], max_response_length=200):
		self.id = id
		self.rate = 1.0 * (15 / 60) # prob / sec
		self.prompt = prompt
		self.max_response_length = max_response_length
		self.waiting = False
		self.started_chats = 0
		self.ended_chats = 0
		self.lock = Lock()

class Sim:
	def __init__(self, num_seconds, base_num_users, load_schedule, streaming, api_key):
		self.users = []

		self.num_seconds = num_seconds
		self.base_num_users = base_num_users
		self.load_schedule = load_schedule
		self.prev_load_idx = -1
		self.etime=2.0

		self.num_users = 0
		
		self.streaming = streaming
		self.client = Client(streaming=streaming, backend="tgi", api_key=api_key)
		self.req_num = 0
		self.proc = psutil.Process(os.getpid())

		self.thread_queue = Queue()
		self.exit_event = Event()
		self.lock = Lock()
		self.bg = Thread(target=self.join_background, args=(self.exit_event, ))
		self.bg.start()

	def add_users(self, num_new_users):
		new_users = []
		user_prompts = random.choices(PROMPTS, weights=[0.3, 0.3, 0.3, 0.1], k=num_new_users)
		for i, up in enumerate(user_prompts):
			new_users.append(User(id=i, prompt=up))
		self.users += new_users
		self.num_users = len(self.users)

	def remove_users(self, num_users_remove):
		new_num_users = max(len(self.users) - num_users_remove, 0)
		self.users = self.users[:new_num_users]
		self.num_users = len(self.users)

	def send_chat(self, user):
		user.lock.acquire()
		prob = user.rate * self.etime
		if (not(user.waiting) and random.random() <= prob):
			request_str = f"{user.id}-{user.ended_chats}"
			# print(f"sending chat: {request_str}")
			prompt = user.prompt
			user.started_chats += 1
			user.waiting = True
			user.lock.release()
			self.client.complete_request(prompt, request_str)
			# print(f"completed chat: {request_str}")
			user.lock.acquire()
			user.ended_chats += 1
			user.waiting = False
		user.lock.release()

	def update_loop(self, i):
		print(f"[sim] updating i = {i} and num fds is: {self.proc.num_fds()}")
		with ThreadPoolExecutor(MAX_CONCURRENCY) as e:
			futures = []
			for user in self.users:
				future = e.submit(self.send_chat, user)
				futures.append(future)

			while len(futures) > 0:
				done, pending = wait(futures, timeout=10, return_when=ALL_COMPLETED)
				print(f"loop {i} has {len(pending)} pending and {len(done)} more done")
				futures = list(pending)

	def update(self, i):
		t = Thread(target=self.update_loop, args=(i,))
		self.thread_queue.put((i, t))
		t.start()

	def join_rest(self):
		while self.thread_queue.qsize() > 0:
			i, t = self.thread_queue.get()
			print(f"joining: {i}")
			t.join()

	def join_background(self, event):
		while not event.is_set():
			while self.thread_queue.qsize() > 0:
				if event.is_set():
					break
				(i, t) = self.thread_queue.get()
				t.join(timeout=JOIN_TIMEOUT)
				if (t.is_alive()):
					self.thread_queue.put((i, t))

			time.sleep(10)

	def update_load(self, time_elapsed):
		load_idx = int((time_elapsed / self.num_seconds) * len(self.load_schedule))
		if load_idx > self.prev_load_idx:
			new_load = self.load_schedule[load_idx] * self.base_num_users
			load_diff = new_load - self.num_users
			if load_diff > 0:
				self.add_users(load_diff)
			else:
				self.remove_users(load_diff * -1)
		self.prev_load_idx = load_idx
	
	def run(self):
		soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
		print(f"[sim] starting, and open file soft limit = {soft_limit}, hard limit= {hard_limit}")
	
		self.client.metrics.session_start_time = time.time()
		lut = self.client.metrics.session_start_time
		time_elapsed = 0.0
		update_num = 0
		while time_elapsed < self.num_seconds:
			self.update_load(time_elapsed)
			now = time.time()
			if now - lut > 1.0:
				self.update(update_num)
				lut = now
				update_num += 1
			time_elapsed = now - self.client.metrics.session_start_time

		self.exit_event.set()
		self.bg.join()
		self.join_rest()

		print("session done")
		self.client.metrics.session_end_time = time.time()
		self.client.metrics.print_metrics()
		self.client.deconstruct()


def main():
	sim = Sim(num_seconds=60 * 3, base_num_users=250, streaming=True, load_schedule=[1, 5, 1], api_key="")
	sim.run()

if __name__ == "__main__":
	main()









