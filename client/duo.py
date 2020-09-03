import re
import mechanize
from apscheduler.schedulers.background import BackgroundScheduler

# Class used to check whether a supplied username/password combo are valid
# MIT Kerberos credentials. Uses mechanize browser to simulate typing in the
# credentials in the duo prompt, then returns the response. Since the browser
# is on the side, just waiting for credentials, this is a lot faster than 
# loading the DUO auth page in a docker container first
class DuoAuth():
    # Note: the mechanize browser instance is passed for thread safety
    def __init__(self, browser):
        self.br = browser#mechanize.Browser()
        self.br.set_handle_robots(False)

        sched = BackgroundScheduler()

        # Refresh the DUO website every 7 minutes
        self.refreshDUO()
        sched.add_job(self.refreshDUO, 'interval', minutes=7)
        sched.start()

    def log(self, val):
        print("[*] DUO_AUTH\t\t" + val)

    # Refreshses the site 
    def refreshDUO(self):
        self.log('Resfreshing duo website...')
        response = self.br.open("https://lms.mitx.mit.edu/auth/login/" \
            + "tpa-saml/?auth_entry=login&next=%2F&idp=mit-kerberos")
        self.log("Duo credential verifier refreshed...")

    # Checks if user/password are valid credentials. Returns true
    # if they are, False if not. If an error occurs, the page is 
    # refreshed and retried indefinitely
    def validateCreds(self, user, password):
        try: 
            self.br.form = list(self.br.forms())[1]
            self.br.form.find_control("j_username").value = user
            self.br.form.find_control("j_password").value = password
            response = self.br.submit()

            if "Duo second-factor authentication is " in str(response.read()):
                self.log("USERNAME PASS FOUND")
                self.br.back()
                return True 

            self.log("USERNAME PASS NOT FOUND")
            return False 
        except Exception as e:
            self.log("Fatal DUO error. Retrying...")
            self.log(e)
            self.refreshDUO()
            return self.validateCreds(user, password, callback)
