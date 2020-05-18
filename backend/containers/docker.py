import random
import subprocess
import pickle
import time
import os

di = os.path.dirname(__file__)
DOCKER_STARTER_CMD = "{}/sh/launch-backend.sh".format(di)
DOCKER_RM_CMD = "{}/sh/close-backend.sh".format(di)
DOCKER_NEWTAB_CMD = "{}/sh/launch-tab.sh".format(di)
DOCKER_INI = "{}/docker.ini".format(di)

class Manager():
	def __init__(self, attack_dom):
		self.attack_dom = attack_dom
		self.backendPool = {}
		tmp = pickle.load(open(DOCKER_INI,"rb")) 
		self.port = tmp["port"]
		# start two back ends 
		self.idle = 0
		self.MIN_CONTAINERS = 5
		self.STARTUP_TIME = 20
		for _ in range(self.MIN_CONTAINERS):
			self.start_backend()
		self.log("# availbale backends:", len(self.backendPool.keys()))

	def log(self, *args):
		print( "DOCKER_MANAGER:"+" ".join(map(str,args)))

	def launch_tab(self, sid, bid, usr, pas):
		cmd = " ".join([DOCKER_NEWTAB_CMD, str(bid), sid, usr, pas])
		self.log("Executing:", cmd)
		cmd = cmd.split(" ")
		self.log("cmd: ", cmd)
		subprocess.Popen(["bash", DOCKER_NEWTAB_CMD, str(bid), sid, usr, pas])

	def claim_backend(self, sid, usr, pas):
		claimedBid = -1
		numIdle = 0
		for bid in self.backendPool.keys():
			if self.backendPool[bid]["status"] == "idle": numIdle += 1

		longest_alive = [-1, -1]
		for bid in self.backendPool.keys():
			candidate = self.backendPool[bid]
			alive = time.time() - candidate["startTime"] 
			if candidate["status"] == "idle" and alive > longest_alive[0]: 
				longest_alive[0] = alive
				longest_alive[1] = bid
		if longest_alive[0] > self.STARTUP_TIME:
			claimedBid = longest_alive[1]

		self.log("available backends: ", self.idle-1, " or ", numIdle-1, "out of", len(self.backendPool.keys()))

		if claimedBid != -1:
			self.idle -= 1
			self.log("backend [bid=",claimedBid,";sid=",sid,"] claimed")
			self.launch_tab(sid, bid, usr, pas)
		else:
			self.log("Could not find suitable backend...")
			if self.idle == 0:
				self.log("No containers available, so starting a new one")
				self.start_backend()
			#self.log("Trying to claim again...")
			#claimedBid = self.claim_backend(sid, usr, pas)
			
		if self.idle <= self.MIN_CONTAINERS:
			self.log("<= ", self.MIN_CONTAINERS, "idle backends... Starting new")
			self.start_backend()

		return claimedBid

	def release_backend(self, bid):
		if bid in self.backendPool.keys():
			if self.backendPool[bid]["status"] == "claimed":
				self.backendPool[bid]["status"] = "idle"
				self.idle += 1
				self.log("released from SID backend:", bid)
			else:
				self.log("WARNING: Cannot release idle backend: ", bid)
		else:
			self.log("WARNING:", bid, "must have already been released...")

	def start_backend(self):
		self.port += 1
		self.backendPool[self.port] = {
			"bid" : self.port,
			"status" : "idle",
			"startTime" : time.time()
		}
		self.idle += 1
		cmd = DOCKER_STARTER_CMD + str(self.port) + " " + str(self.port) + " " + self.attack_dom
		self.log("Executing", cmd)
		self.log("View at: http://localhost:" + str(self.port))
		self.log("cmd:", cmd.split(" "))
		subprocess.Popen(["bash", DOCKER_STARTER_CMD, str(self.port), str(self.port), self.attack_dom])
		pickle.dump({"port":self.port}, open(DOCKER_INI, "wb"))

	def stop_backend(self, bid, name):
		bid = int(bid)
		cmd = "docker stop firefoxSID" + str(bid)
		self.log("Executing:", cmd)
		self.log("Saved successful container: " + str(bid) + " : " + name)

		try:
			for b in self.backendPool.keys():
				self.log("KEY exists:", b)
			self.backendPool.pop(bid)
			if self.backendPool[bid]["status"] == "idle":
				self.idle -= 1	
		finally: 
			subprocess.Popen(["docker", "stop", "firefoxSID" + str(bid)])
	
	def close_all(self):
		for bid in self.backendPool.keys():
			self.delete_backend(bid)

	def delete_backend(self, ID):
		cmd = DOCKER_RM_CMD + str(ID)
		self.log("Executing:", cmd)
		subprocess.Popen(["bash", DOCKER_RM_CMD, str(ID)])


