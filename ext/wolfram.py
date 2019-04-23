import json
from . import commands
import requests

class Wolfram(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("wolfram")
		self.inter = True
	
	def onStart(self):
		dl = self.host.config._get('disabled')	
		if self.cfg._get('wolfram_appid', "") == "" and type(self).__name__ not in dl:
			print("Wolfram disabled, missing appid. (Config set wolfram_appid)")
			

			self.host.command_cache[type(self).__name__].onClose()
			dl.append(type(self).__name__)
			self.host.config._set('disabled', dl)
		else:
			self.appid = self.cfg._get('wolfram_appid', "")
			
	def onTrigger(self, value = ""):
		f = f"http://api.wolframalpha.com/v1/conversation.jsp?appid={self.appid}&i={value.replace(' ', '+')}"
		r = requests.get(f).text
		try:
			msg = json.loads(r)
			if msg.get('error'):
				return self.message(msg['error'])
			return self.message(msg['result'])
		except Exception as e:
			return self.output(f"{type(e)}\n{e}\n{r}")
