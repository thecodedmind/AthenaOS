import arrow
from . import commands
from humanfriendly import format_timespan, parse_timespan

class TimerManager:
	def __init__(self, host):
		self.host = host
		
	def get(self):
		self.host.config.load()
		return self.host.config._get('timers', [])
	
	def setTimers(self, new_list):
		self.host.getProcess('TimerWatcher').update(new_list)
		
		self.host.restartProcess('TimerWatcher')
		
	def triggerAt(self, timestamp, message = ""):
		timers = self.get()
		
		if message:
			print(f"Got message {message}")
			
		if ":" in timestamp:
			h = timestamp.split(":")[0]
			m = timestamp.split(":")[1]
			if h.isdigit() and m.isdigit():
				validated = arrow.now().replace(hour=int(h), minute=int(m))
				
				if validated <= arrow.now():
					return -2
		
				fnow = f"{arrow.now().year}/{self.zerospace(arrow.now().month)}/{self.zerospace(arrow.now().day)} {self.zerospace(arrow.now().hour)}:{self.zerospace(arrow.now().minute)}:{self.zerospace(arrow.now().second)}"		

				formatted = f"{validated.year}/{self.zerospace(validated.month)}/{self.zerospace(validated.day)} {self.zerospace(validated.hour)}:{self.zerospace(validated.minute)}:{self.zerospace(validated.second)}"
				data = {'timestamp': formatted, 'created_at': fnow, 'message': message}
				timers.append(data)
				self.setTimers(timers)
				
				index = timers.index(data)
				#check for if the date has passed, if yes, shift it one day forward then process
				return index #when complete, return the index number
		
		return -1
	
	def triggerIn(self, form, message = ""):
		timers = self.get()
		
		if message:
			print(f"Got message {message}")		
		values = form.split()
		total_seconds = 0
		for item in values:
			total_seconds += parse_timespan(item)
		
		validated = arrow.now().shift(seconds=+total_seconds)
		if validated <= arrow.now():
			return -2
		
		fnow = f"{arrow.now().year}/{self.zerospace(arrow.now().month)}/{self.zerospace(arrow.now().day)} {self.zerospace(arrow.now().hour)}:{self.zerospace(arrow.now().minute)}:{self.zerospace(arrow.now().second)}"
		
		formatted = f"{validated.year}/{self.zerospace(validated.month)}/{self.zerospace(validated.day)} {self.zerospace(validated.hour)}:{self.zerospace(validated.minute)}:{self.zerospace(validated.second)}"
		
		data = {'timestamp': formatted, 'created_at': fnow, 'message': message}
		timers.append(data)
		self.setTimers(timers)
		
		index = timers.index(data)
		#check for if the date has passed, if yes, shift it one day forward then process
		return index #when complete, return the index number
	
	def zerospace(self, num):
		if num < 10:
			return f"0{num}"
		else:
			return f"{num}"
		
	def stop(self, index):
		timers = self.get()
		#print(timers)
		try:
			del timers[index]
			self.setTimers(timers)
			return True
		except Exception as e:
			print(e)
		
		return False
	
class TimerCommand(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("timers")
		self.addListener("timer")
		self.inter = True
		self.tman = TimerManager(self.host)
		
	def onTrigger(self, value = ""):
		b = self.host.formatting.Bold
		g = self.host.colours.F_Green
		bl = self.host.colours.F_Blue
		r = self.host.reset_f
		if value == "":
			value = "list"
		if value.startswith("at "):
			value = value[3:]
			message = ""
			if "--" in value:
				message = value.split("--")[1].strip()
				value = value.split("--")[0].strip()
				
			f = self.tman.triggerAt(value, message)
			if f == -1:
				return self.message("Bad formatting. Format is hh:mm.")			
			if f == -2:
				return self.message("That time has passed.")
			return self.message(f"Timer created at index {f}")
		
		if value.startswith("in "):
			value = value[3:]
			message = ""
			if "--" in value:
				message = value.split("--")[1].strip()
				value = value.split("--")[0].strip()
			f = self.tman.triggerIn(value, message)

			if f == -2:
				return self.message("That time has passed.")			
			
			return self.message(f"Timer created at index {f}")

		if value.startswith("for "):
			value = value[4:]
			message = ""
			if "--" in value:
				message = value.split("--")[1].strip()
				value = value.split("--")[0].strip()
			f = self.tman.triggerIn(value, message)

			if f == -2:
				return self.message("That time has passed.")			
			
			return self.message(f"Timer created at index {f}")
		
		if value.startswith("stop "):
			value = value[5:]
			if value == "all":
				self.tman.setTimers([])
				return self.message("Timers cleared.")
			
			if value.isdigit():
				value = int(value)
				if self.tman.stop(value):
					return self.message("Timer ended.")
				else:
					return self.message("No timer found.")
			else:
				return self.message("Value must be a number.")
			
		if value == "list":
			s = ""
			for item in self.tman.get():
				index = self.tman.get().index(item)
				
				now = arrow.now()
				form = arrow.get(f"{item['timestamp']} local", 'YYYY/MM/DD HH:mm:ss ZZZ')
				seconds = form - now
				s += f" {b}[{index}]{r} {g}{item['timestamp']}{r} - Created at {g}{item['created_at']}{r} ({bl}{item['message']}{r})\nExpires {form.humanize()}\n\n"
			if s != "":
				s = f"\n{s}"
				return self.output(s[:-1])
			else:
				return self.message("No timers exist.")
			
"""
commands module file:
	timerManager - non-command class holding the info
		* .start(timestamp) - adds to a list
		* .stop(id) - deletes from list
		
	timerCommand1.a - alert me in x about y (split at about, everything after is the message)
	timerCommand1.b - alert me at x about y

	timerCommand2 - generic "stop a timer"
		holds to check for ID, do my prompt system to list the timers and their index

	timerCommand3 - generic "show timers"
		lists active timers from Manager list

	timerCommand4 - interpreted manager
		* timer start value - calls to manager.start(value)
		* timer stop value - calls to manager.stop(value)
		* timer list - shows active timers
"""
