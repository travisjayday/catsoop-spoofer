import re
import mechanize
from apscheduler.schedulers.background import BackgroundScheduler

class DUOAuth():
	def __init__(self):
		self.br = mechanize.Browser()
		self.br.set_handle_robots(False)

		sched = BackgroundScheduler()

		# seconds can be replaced with minutes, hours, or days
		self.refreshDUO()
		sched.add_job(self.refreshDUO, 'interval', minutes=7)
		sched.start()

	def refreshDUO(self):
		print('resfreshing duo website...')
		response = self.br.open("https://lms.mitx.mit.edu/auth/login/tpa-saml/?auth_entry=login&next=%2F&idp=mit-kerberos")
		print("duo refreshed...")

	def validateCreds(self, user, password, callback):
		try: 
			self.br.form = list(self.br.forms())[1]
			self.br.form.find_control("j_username").value = user
			self.br.form.find_control("j_password").value = password
			response = self.br.submit()

			if "Duo second-factor authentication is requir" in str(response.read()):
				print("USERNAME PASS FOUND")
				self.br.back()
				callback(True)
				return True 
			else:
				print("USERNAME PASS NOT FOUND")
				callback(False)
				return False 
		except:
			print("Fatal DUO error. Retrying...")
			self.refreshDUO()
			self.validateCreds(user, password, callback)
