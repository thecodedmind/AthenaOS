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
		en = tkinter.Entry(self.query)
		en.pack()
		sub = ttk.Button(self.query, "Limit", command=lambda e: self.submitLimit(process, en.get()))
		sub.pack()
		
	def submitLimit(self, process, limit):
		os.system(f"{self.host.scriptdir}bin/cpulimit --pid {process} --limit {limit}&")

	def onTrigger(self):
		while True:
			sleep(self.host.config._get('assistant_delay', 10))
			if self.host.config._get('assistant_cpu', False):
				for p in psutil.process_iter():
					if p.username() == os.environ.get('USER'):
						cpu = p.cpu_percent(self.host.config._get('assistant_cpu_time', 5))
						if cpu > self.host.config._get('auto_cpu_limit', 50):
							n = p.name()
							self.alert = tkinter.Tk()
							label = tkinter.Label(self.alert, text=f"{p.name()} is using {cpu}% CPU.").pack()
							
							killbutton = ttk.Button(self.alert, text="Kill", command=lambda e: killProcess(p.pid)).pack()
							limitbutton = ttk.Button(self.alert, text="Limit", command=lambda e: limitQuery(p.pid)).pack()
							ignorebutton = ttk.Button(self.alert, text="Ignore", command=lambda e: self.alert.destroy()).pack()
							f = self.alert.mainloop()
