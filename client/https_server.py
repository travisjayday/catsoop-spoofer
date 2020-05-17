from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import sys
import os
import threading

class SilentHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return

def startServer(host):
	key = os.path.abspath(os.path.dirname(__file__) + '/../ssl/key.pem')
	crt = os.path.abspath(os.path.dirname(__file__) + '/../ssl/cert.pem')
	print("Using key", key)
	print("Using certificate", crt)

	web_dir = os.path.join(os.path.dirname(__file__), 'public')
	os.chdir(web_dir)
			
	print("Trying to host https server on", host + ":443")
	httpd = HTTPServer((host, 443), SilentHTTPRequestHandler)

	httpd.socket = ssl.wrap_socket (httpd.socket, 
			keyfile=key, 
			certfile=crt, server_side=True)

	threading.Thread(target=httpd.serve_forever).start()
