
## Vulnerability 0 \[aka CVE-CATXSS-6-1-2020\]
### Note: This has been fixed in the latest dev Snapshot of CATSOOP. See CVE-CATXSS-9-1-2020 for a Fall 2020 attack vector.

All modern catsoop powered sites suffer from an XSS vulnerability that allows for arbitrary client-side code execution. 

Cause: 
When loading the 404 page not found, catsoop does not sanitize the URL and displays it in the raw html page. 

Proof of concept: 
`https://6002.catsoop.org/%3Cscript%3Ealert(1)%3C/script%3E`

Fix: 
Simply sanitize the url before displaying it. 

Status: 
**Patched**

## Vulnerability 1 \[aka CVE-CATXSS-9-1-2020\]

Modern catsoop sites that reflect query string parameters on the page are vulnerable. 

Cause:
HTTP Get query key/value pairs in the URL do not get sanitized. If these values get directly displayed on the page, we have an XSS attack vector.

Proof of concept:
The 6.009 site uses the vulnerable query parameters for the recitation page: `https://py.mit.edu/fall20/recitation?rec=%3cscript%3ealert(1)%3c/script%3e`

Tested on:
- Client: iOS/Chrome+Safari, Android/Chrome, Windows/Chrome, MacOS/Chrome+Safari
- DUO: iOS calls, Android calls + pushes
- CATSOOP domain: py.mit.edu / CAT-SOOP v2021.2.0.dev8 ("Devon Rex" development snapshot).

Status: 
**Vulnerable/Ongoing**

## Exploiting
Through these XSS (Cross-Site-Scripting) vulnerabilites, we achieve arbitrary client-side code injection to thus harvest DUO credentials by bypassing the 2FA (two-factor authentication). That's what this repository is for. But we don't just harvest credentials -- with a little bit of docker magic, we can even steal 30-day DUO sessions, meaning we'd have our victim fully compromised for 30 days. We could access their MIT Websis, their Zoom, their Atlas, their E-Mails, their MITPay, and more. How does it work? Man-in-the-middle with Docker virtualized container backends.

The key components of this attack include: 

- A spoofed front-end for the victim (html, css, js) 
- A tcp websocket server (python) 
- A python browser (mechanize) 
- A docker container orchestration mechanism (python) 
- Docker containers that run firefox and have a custom firefox extension loaded that connects to attackers websocket server (bash, html, css, js)

## Example Attack Flow
                         
![](/readme/graph.png)
                                                                             
1. User happily opens malicious URL because he's connecting to a familiar catsoop / mit.edu site 
2. Through the XSS, we inject a webpage that the user expects (a clone of the catsoop site, callend `entry-site` located in `/client/public/entry-site`)
3. The user clicks on the familiar login button and is redirected to the fake DUO login page. Note: this spoof simulates page buffering and features exact copies of the DUO auth flow (located in `/client/public/idp/Authn`). \*
4. After inputting his credentials, the victim's browser opens a websocket session with the attacker's machine who quickly verifies the credentials using a python browser. 
5. If the credentials were right, the server chooses one of many running docker containers and assigns the victim to that container. The container is running a firefox instance (can be accessed with VNC at ```localhost:BID``` where BID is the backend ID of a container) and a custom firefox extension (located in `/backend/containers/firefox/duo-login-ext`). 
6. The assigned container goes to a real DUO login page and injects the victim's credentials. At this point, the victim and the container are synced: They are both at the DUO prompt where the victim has to choose an authentication method (phone call or DUO push if available. User information such as phone number and device type is communicated in realtime between backend and victim with the attacker's machine as middle-man). 
7. The user chooses an auth method, his choice is relayed to the docker backend through the websocket server, and the docker backend makes that choice on the real DUO site. 
8. The user will get a call or push from DUO, thinking that he made the request EVEN THOUGH THE DOCKER CONTAINED FIREFOX DID. \*\*
9. The user authenticates the DUO request with his phone and gets re-directed to either (`/client/public/exit-site`) or the REAL, original catsoop.org page (this can be configured). In the future, if he tries to click the malicious link again, he will be auto-redirected to the legit catsoop site. 
10. The docker container that was succesfully logged into is shutdown and saved. An entry to it's firefox profile is made in the attacker's firefox profiles list. 
11. The attacker goes to his firefox, changes his profile to the victim profile, and now has access to everything that requires DUO authentication.

\*Note: The only difference is the URL displayed in the browser. The domain `idp.mit.edu` is replaced by the corresponding vulnerable `catsoop.org` or `mit.edu` domain. Only very keen victims might notice this difference. Also note that mobile DUO is supported / spoofed (e.g. Android, iOS).
\*\*Note: If the victim chose DUO push AND he expands the notification or opens it in the app, he might notice that the request came from a different geographical location IFF the victim and attacker are in different cities. Again, only keen Android users might notice this since DUO Push is not available on iOS.  

## Important Source Files
The primary XSS injection payload (which gets injected multiple times throughout the flow): ![/client/payload.js](/client/payload.js)

The https server: ![/client/https_server.py](/client/https_server.py)

The victim's socket client: ![/client/public/idp/Authn/remote-bridge.js](/client/public/idp/Authn/remote-bridge.js), ![/client/public/idp/Authn/remote-bridge-2.js](/client/public/idp/Authn/remote-bridge-2.js)

The websocket server: ![/backend/socket_server.py](/backend/socket_server.py)

The docker ochrestrator: ![/backend/containers/docker.py](/backend/containers/docker.py)

The firefox extension (loaded in the docker container): ![/backend/containers/firefox/duo-login-ext](/backend/containers/firefox/duo-login-ext)

## Dependencies
python3 packages (can be installed with pip):
```
websockets
mechanize
apscheduler
```
Docker: 
Visit https://docs.docker.com/engine/install/ubuntu for installation instructions

## Network Configuration
To spoof a catsoop website, you need an https domain pointing to your machine. The setup requires 

```
https://attacker-domain.com:443 --> localhost:443
wss://attacker-domain.com:80 --> localhost:80
```

There are free DNS sites like https://freenom.com that let you create your `attacker-domain` and route it to your public IP (use port forwarding on your router obviously).

Place your SSL certificates in the `/ssl` forder. You will need the files `cert.pem` and `key.pem` in the `ssl` folder. Use a certificate authority to generate these (don't genereate them yourself). There are free sites like https://www.sslforfree.com/ that do this for you. I recommend using certbot from Let's Encrypt. 

Note `cert.pem` is the public certificate file and may be originally named `certificate.crt` or `cert.crt`. `key.pem` is the private key and may be originally named `private.key`. 

Note: If for some reason your docker container's firefoxes have issues with your certificate, you can create an entry in firefoxSID/profile/cert\_override.txt to add a manual exception to certs. This should generally not be the case, however. 
                                                                                                                                        
## Modifying the Spoof
After making changes you should generally run `configure.py` again. However:
- If you just make changes to the Firefox extension, you can just run `./make-zips.sh` and that will re-pack the extension.
- If you want to make temporary changes to the payload, you can modify files in the `client/public` directory as desired. The main payload is either in `client/public/'\</pre` or in `client/public/index.html` depending on which exploit/CVE you configured with. 

## Running the Spoof
Configure the entrance, exit website, and other environment variables by running

`sudo python3 configure.py https://entryurl.co https://exiturl.co`

To run the spoof, execute 

`sudo run-spoof.py`

or 

`sudo nohup python3 -u run-spoof.py LOCAL_IP &`

if you want to run it from an SSH session (server mode) 

## Questions
Please raise an issue if you have a question or if something is not working. 

## Liability
Note that this whole repository is for educational purposes only. I wanted to see how far I could take a simple XSS vulnerability and share my findings. By no means am I, Travis Ziegler, responsible for other people maliciously applying my work. 
