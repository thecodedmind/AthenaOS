from . import processes
import tkinter
from tkinter import ttk, messagebox
import arrow
from time import sleep
import copy

class TimerWatcher(processes.AOSProcess): 
	def onStart(self):
		self.timers = self.host.cfgget('timers')
		
	def update(self, new_list):
		self.host.cfgset('timers', new_list)
		self.timers = new_list
		
	def onTrigger(self):
		while True:
			if len(self.timers) > 0:
				sleep(1)
			else:
				sleep(60)

			procs = []
			for item in self.timers:
				now = arrow.now()
				form = arrow.get(f"{item['timestamp']} local", 'YYYY/MM/DD HH:mm:ss ZZZ')
				if form <= arrow.now():
					message = ""
					if item['message']:
						message = f"\n{item['message']}"
						
					res = f"The timer for {item['timestamp']} that was created at {item['created_at']} has expired!{message}"
					
					
					procs.append(item)
					tk = tkinter.Tk()
					tk.title("Alerts")
					tLabel = tkinter.Label(tk, text=res).pack()
					
					f = tk.mainloop()
			if len(procs) > 0:
				for item in procs:
					self.timers.remove(item)
					
				self.host.cfgset('timers', self.timers)
					
