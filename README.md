# Note: This has been fixed in the latest dev Snapshot of CATSOOP

## Vulnerability
All modern catsoop powered sites suffer from a neat XSS vulnerability that allows for arbitrary client-side code execution. 

Cause: 
When loading the 404 page not found, catsoop does not sanitize the URL and displays it in the raw html page. 

Proof of concept: 
`https://6002.catsoop.org/%3Cscript%3Ealert(1)%3C/script%3E`

Fix: 
Simply sanitize the url before displaying it. 

Remark: 
Please don't tell the catsoop people about this yet, as this is still a work in progress and I haven't yet stolen my friend's credentials.

## Exploiting
Because of this arbitrary code injection, we can harvest DUO credentials! That's what this repo is for. But not just credentials -- with a little bit of docker magic, we can harvest 30 day DUO sessions, meaning we'd have our victim fully compromised. We could access their websis, their Zoom, their Atlas, their E-Mails, and more. How does it work? Man-in-the-middle with Docker backends.

The key components of this attack include: 

- A spoofed front-end for the victim (html, css, js) 
- A tcp websocket server (python) 
- A python browser (mechanize) 
- A docker container orchestration mechanism (python) 
- Docker containers that run firefox and have a custom firefox extension loaded that connects to attackers websocket server (bash, html, css, js)

## Example Attack Flow
                         
![](/readme/graph.png)
                                                                             
1. User happily opens malicious URL because he's connecting to a familiar catsoop site 
2. Through the XSS, we inject a webpage that the user expects (a clone of the catsoop site, callend `entry-site` located in `/client/public/entry-site`)
3. The user clicks on the familiar login button and is redirected to the DUO login page. Note: this spoof simulates page loads and features exact copies of the DUO auth flow (located in `/client/public/idp/Authn`). \*
4. After inputting his credentials, victim's browser opens a websocket session with the attacker's machine who verifies the credentials using a python browser. 
5. If the credentials were right, the server chooses one of many running docker containers and assigns the victim to that container. The container is running a firefox instance (can be accessed with VNC) and a custom firefox extension (located in `/backend/containers/firefox/duo-login-ext`). 
6. The assigned container goes to a DUO login page and injects the victim's credentials. At this point, the victim and the container are synced: They are both at the DUO prompt where the victim has to choose an authentication method (phone call or DUO push). 
7. The user chooses an auth method, his choice is relayed to the docker backend through the websocket server, and the docker backend makes that choice on the real DUO site. 
8. The user will get a call or push from DUO, thinking that he made the request EVEN THOUGH THE DOCKER CONTAINED FIREFOX DID. \*\*
9. The user authenticates the DUO request with his phone and gets re-directed to either (`/client/public/exit-site`) or the REAL, original catsoop.org page (this can be configured at will). In the future, if he tries to click the malicious link again, he will be auto-redirected to the legit catsoop site. 
10. The docker container that was succesfully logged into is shutdown and saved. An entry to it's firefox profile is made into the attacker's firefox profiles list. 
11. The attacker goes to his firefox, changes his profile to the victim profile, and now has access to everything that requires DUO authentication.

\*Note: The only difference is the URL displayed in the browser. The domain `idp.mit.edu` is replaced by the corresponding vulnerable `catsoop.org` domain. Only very keen victims might notice this difference. Also note that mobile DUO is supported / spoofed.  
\*\*Note: If the victim chose DUO push AND he expands the notification or opens it in the app, he might notice that the request came from a different geographical location IFF the victim and attacker are in different cities. 

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

Place your SSL certificates in the `/ssl` forder. You will need the files `cert.pem` and `key.pem` in the `ssl` folder. Use a certificate authority to generate these (don't genereate them yourself). There are free sites like https://www.sslforfree.com/ that do this for you.
                                                                                                                                        
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
