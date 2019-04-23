from . import commands
import os

class AppImageManager(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)	
		self.addListener("appimage")
		self.addListener("aim")
		self.inter = True

	def onStart(self):
		self.apps = []
		self.apps_path = self.host.config._get('appimage_path')
		print("Building appimages cache...")
		if not self.apps_path:
			self.host.printf("No appimage path is defined, use 'set appimage path to' followed by a path to the appimage directory you want to use.", tag='info')
			self.disabled = True
			return
		
		for file in os.listdir(self.apps_path):
			filename = os.fsdecode(file)
			if filename.lower().endswith(".appimage"):
				self.apps.append(filename)	
	
	def onClose(self):
		self.apps = []
		
	def onTrigger(self, value=""):
		if self.disabled:
			return self.message("No appimage path is defined, use 'set appimage path to' followed by a path to the appimage directory you want to use.")
		
		if value == "":
			value = "list"
			
		self.apps_path = self.host.config._get('appimage_path')
		
		if value == "reload":
			self.onStart()
			
		if value == "list":
			if len(self.apps) == 0:
				return self.message("No appimages were found.")
				
			s =  ""
			for item in self.apps:
				s += f"{item}\n"
				
			return self.output(s[:-1])
		
		if value.startswith("run "):
			print(value)
			value = value[4:]
			print(value)
			os.system(f'{self.apps_path}{value}*&')
 
