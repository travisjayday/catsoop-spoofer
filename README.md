# Dependencies
python3 packages (can be installed with pip):
```
websockets
mechanize
apscheduler
```
Docker: 
Visit https://docs.docker.com/engine/install/ubuntu for installation instructions

# Network Configuration
To spoof a catsoop website, you need an https domain pointing to your machine. The setup requires 

```
https://attacker-domain.com:443 --> localhost:443
wss://attacker-domain.com:80 --> localhost:80
```

As a recommendation, 

# Running the Spoof
Configure the entrance, exit website, and other environment variables by running

`sudo python3 configure.py https://entryurl.co https://exiturl.co`

To run the spoof, execute 

`sudo run-spoof.py`

or 

`sudo nohup python3 -u run-spoof.py LOCAL_IP &`

if you want to run it from an SSH session (server mode) 
