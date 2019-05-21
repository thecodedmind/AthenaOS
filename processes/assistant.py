from . import processes
import psutil
from time import sleep
import tkinter
from tkinter import ttk
import os

def killProcess(ident):
	try:
		if str(ident).isdigit():
			process = psutil.Process(int(ident)).kill()
			return True
		else:
			for p in psutil.process_iter():
				if p.name() == str(ident):
					p.kill()
	except Exception as e:
		print(e)
		return False
	
class Assistant(processes.AOSProcess):
	def limitQuery(self, process):
		#self.alert.destroy()
		self.query = tkinter.Toplevel()
		self.query.title("CPU Limiter")
		en = tkinter.Entry(self.query)
		en.pack()
		sub = ttk.Button(self.query, text="Limit", command=lambda: self.submitLimit(process, en.get()))
		sub.pack()
		
	def submitLimit(self, process, limit):
		os.system(f"{self.host.scriptdir}bin/cpulimit --pid {process} --limit {limit}&")
		self.query.destroy()
		self.alert.destroy()
		
	def addNoNotify(self, process):
		ignores = self.host.config._get('assistant_cpu_ignores', [])
		ignores.append(process.name())
		#print(ignores)
		self.host.cfgset('assistant_cpu_ignores', ignores)
		self.query = tkinter.Toplevel()
		en = tkinter.Label(self.query, text="Process ignored, click 'Okay' to close all dialog boxes.")
		en.pack()
		sub = ttk.Button(self.query, text="Okay", command=lambda: self.closeDialogs([self.query, self.alert]))
		sub.pack()
	
	def closeDialogs(self, dialogs):
		for item in dialogs:
			item.destroy()
			
	def onTrigger(self):
		while True:
			sleep(self.host.config._get('assistant_delay', 10))
			if self.host.config._get('assistant_cpu', False):
				for p in psutil.process_iter():
					if p.username() == os.environ.get('USER'):
						cpu = p.cpu_percent(self.host.config._get('assistant_cpu_time', 5))
						if cpu > self.host.config._get('auto_cpu_limit', 50) and p.name() not in self.host.config._get('assistant_cpu_ignores', []):
							n = p.name()
							self.alert = tkinter.Tk()
							self.alert.title("CPU Monitor")
							label = tkinter.Label(self.alert, text=f"{p.name()} is using {cpu}% CPU.").pack()
							
							killbutton = ttk.Button(self.alert, text="Kill", command=lambda: killProcess(p.pid)).pack(side="right", fill="x", expand=True)
							
							limitbutton = ttk.Button(self.alert, text="Limit", command=lambda: self.limitQuery(p.pid)).pack(side="right", fill="x", expand=True)
							
							ignorebuttonf = ttk.Button(self.alert, text="Ignore Permenantly", command=lambda: self.addNoNotify(p)).pack(side="right", fill="x", expand=True)
							
							ignorebutton = ttk.Button(self.alert, text="Ignore", command=lambda: self.alert.destroy()).pack(side="right", fill="x", expand=True)
							
							f = self.alert.mainloop()
