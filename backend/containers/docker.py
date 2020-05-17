import random
import pickle
import time
import os

di = os.path.dirname(__file__)
DOCKER_STARTER_CMD = "bash {}/sh/launch-backend.sh ".format(di)
DOCKER_RM_CMD = "bash {}/sh/close-backend.sh ".format(di)
DOCKER_NEWTAB_CMD = "bash {}/sh/launch-tab.sh ".format(di)
DOCKER_INI = "{}/docker.ini".format(di)

class Manager():
	def __init__(self, attack_dom):
		self.attack_dom = attack_dom
		self.backendPool = {}
		tmp = pickle.load(open(DOCKER_INI,"rb")) 
		self.port = tmp["port"]
		# start two back ends 
		self.idle = 0
		self.start_backend()
		self.start_backend()
		self.log("# availbale backends:", len(self.backendPool.keys()))

	def log(self, *args):
		print( "DOCKER_MANAGER:"+" ".join(map(str,args)))

	def launch_tab(self, sid, bid, usr, pas):
		cmd = " ".join([DOCKER_NEWTAB_CMD, str(bid), sid, usr, pas])
		self.log("Executing:", cmd)
		os.system(cmd)

	def claim_backend(self, sid, usr, pas):
		claimedBid = -1
		numIdle = 0
		for bid in self.backendPool.keys():
			if self.backendPool[bid]["status"] == "idle": numIdle += 1

		for bid in self.backendPool.keys():
			self.log(self.backendPool[bid])
			candidate = self.backendPool[bid]
			if candidate["status"] == "idle" and time.time() - candidate["startTime"] > 7:
				candidate["status"] = "claimed"
				claimedBid = bid
				break
		self.log("available backends: ", self.idle-1, " or ", numIdle-1, "out of", len(self.backendPool.keys()))

		if claimedBid != -1:
			self.idle -= 1
			self.log("backend [bid=",claimedBid,";sid=",sid,"] claimed")
			self.launch_tab(sid, bid, usr, pas)
		else:
			self.log("Could not find suitable backend... Retrying in 3 seconds...")
			if self.idle == 0:
				self.log("No containers available, so starting a new one")
				self.start_backend()
			time.sleep(3)
			self.log("Trying to claim again...")
			claimedBid = self.claim_backend(sid, usr, pas)
			
		if self.idle <= 1:
			self.log("<= 1 idle backends... Starting new")
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
		os.system(cmd)
		pickle.dump({"port":self.port}, open(DOCKER_INI, "wb"))


	def stop_backend(self, bid, name):
		cmd = "docker stop firefoxSID" + str(bid)
		if self.backendPool[bid]["status"] == "idle":
			self.idle -= 1	
		del self.backendPool[bid]
		self.log("Executing:", cmd)
		self.log("Saved successful container: " + str(bid) + " : " + name)
		os.system(cmd)
	
	def close_all(self):
		for bid in self.backendPool.keys():
			self.delete_backend(bid)

	def delete_backend(self, ID):
		cmd = DOCKER_RM_CMD + str(ID)
		self.log("Executing:", cmd)
		os.system(cmd)


