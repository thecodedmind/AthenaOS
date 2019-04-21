from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from dataclasses import dataclass
from typing import Any
import os
import humanfriendly
import humanfriendly.prompts
from Color import *
import json
import requests

class BaseCommand:
	"""
	Template for creating new commands
	Commands are to be placed in a .py file in the /ext directory.
	Command classes inside that file should extend BaseCommand.
	Give phrases to the self.phrases variable in the format of
	self.phrases = {'message': 'Trigger message here', 'check':100}
	check is the percentage match needed to make the script understand this message is the one being searched for
	
	self.inter defines wether the command is standalone or interpreted
	inter as True means interpreted, and takes any text after the command message as a value for the command
	inter as False means standalone, the command runs as-is
	
	self.alias defines an alias, only used for Help searching for now.
	"""
	def __init__(self, host):
		self.phrases = []
		self.inter = False
		self.host = host
		self.alias = type(self).__name__
		self.hidden = False
		self.disabled = False
		self.cfg = self.host.config
		
	def addListener(self, text, check = 100):
		#Helper function for adding listeners
		data = {'message': text, 'check': check}
		if data in self.phrases:
			printf(f"Ignoring duplicate listener for {self.name}.\n{data}", tag='output')
			return
		
		self.phrases.append(data)
		
	def message(self, text):
		#Helper function for quick access to returning just a message.
		return {'message': text}
	
	def output(self, text):
		#Helper function for quick access to returning just an output to console.
		return {'output': text}
	
	def getHelp(self):
		if self.__doc__ != "":
			return self.__doc__
		else:
			return "No help string set."
		
	def check(self, check_message):
		if type(self).__name__ in self.host.config._get('disabled'):
			#print("Disabled command.")
			return False
		
		for item in self.phrases:
			if not self.inter:
				if fuzz.ratio(check_message.lower(), item['message'].lower()) >= item['check']:
					#print(f"{type(self).__name__} checked")
					return	{'ratio': fuzz.ratio(check_message.lower(), item['message'].lower())}
			else:
				if check_message.lower().startswith(item['message'].lower()):
					return {'ratio': fuzz.ratio(check_message.lower(), item['message'].lower())}
	
	def onTrigger(self, value = ""):
		"""Called when the command is executed."""
		self.onTrigger(self, value)
	
	def hold(self, message):
		"""Helper function to set the command in to hold mode, waiting for a response"""
		return {'message': message, 'code': 'hold', 'held': self}
	
	def onHold(self, value):
		"""Like onTrigger but ran after being held"""
		pass
	
	def onStart(self):
		"""Run on startup."""
		pass
	
	def onClose(self):
		"""Run on shutdown"""
		pass
		
class WaitTemplate(BaseCommand):
	"""
	Template for handling Wait commands
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'wait'}, {'message':'hold'}]
		self.inter = True
		self.hidden = True
		
	def onTrigger(self, value = ""):
		return self.hold("Hold what?")
	
	def onHeld(self, value):
		self.host.say(f"You said {value}.")
	
class Quit(BaseCommand):
	"""
	This command closes the script.
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'quit', 'check': 100}, {'message': 'exit', 'check': 100}]
	
	def onTrigger(self, value = ""):
		if self.host.promptConfirm("Are you sure?"):
			return {'message': 'Goodbye.', 'code': 'quit'}
		else:
			return self.message("Okay, nevermind then.")
	
class FallbackManager(BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'fallback'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		c = ""
		for item in self.host.commands:
			not_allowed = ['basecommand', 'fallbackmanager', 'quit', 'waittemplate']
			if not self.host.command_cache[item[0]].hidden and item[0].lower() not in not_allowed and item[0] not in self.host.config._get('disabled'):
				if value.lower() in item[0].lower():
					c = self.host.command_cache[item[0]]
					self.cfg._set('fallback', item[0])
					return self.message(f"{item[0]} set as fallback.")
				
class CommandsList(BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'commands', 'check': 95}]
		
	def onTrigger(self):
		c = ""
		for item in self.host.commands:
			if not self.host.command_cache[item[0]].hidden and item[0].lower() != "basecommand":
				if item[0] in self.host.config._get('disabled'):
					c += f" [\x1b[31mOFF\x1b[0m] {self.host.command_cache[item[0]].__class__.__module__}.{item[0]}\n"
				else:
					c += f" [\x1b[32mON\x1b[0m] {self.host.command_cache[item[0]].__class__.__module__}.{item[0]}\n"
		
		return self.output(c[:-1])
			
class Help(BaseCommand):
	"""
	This is a help.
	Format: help <command>
	Searches by the command triggers
	[BASE]
	~Kaiser
	"""
	
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'help'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		if value == "":
			c = ""
			for item in self.host.commands:
				if not self.host.command_cache[item[0]].hidden and self.host.command_cache[item[0]].getHelp() and item[0].lower() != "basecommand":
					c += f"{item[0]} [{self.host.command_cache[item[0]].__class__.__module__}]\n{self.host.command_cache[item[0]].getHelp()}\n\n"
			
			holding = self.hold("Say a command name now for help on that command.")
			holding['output'] = c
			return holding
		
		for item in self.host.commands:
			inst = self.host.command_cache[item[0]]#item[1](self.host)
			if inst.check(value) or value == item[0]:#if value.lower() == item[0].lower() or value.lower() == inst.alias:
				return {'output': inst.getHelp()}
			
	def onHeld(self, value):
		if value == "cancel" or value == "":
			return {'message': "Cancelling help menu."}
		
		for item in self.host.commands:
			inst = self.host.command_cache[item[0]]#item[1](self.host)
			if inst.check(value) or value == item[0]:#if value.lower() == item[0].lower() or value.lower() == inst.alias:
				return {'output': inst.getHelp()}
			
		return self.hold("That command wasn't found, try again?")
	
class Task(BaseCommand):
	"""
	Task manager
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'task'}, {'message': 'process'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		if value == "":
			value = "list"
		if value.startswith("start "):
			task = value.split(" ")[1]
			res = self.host.startProcess(task)
			
			if res:
				return {'message': f"Started process {task}"}
			else:
				return {'message': f"Problem starting {task}, already running or does not exist."}
			
		elif value.startswith("stop "):
			task = value.split(" ")[1]
			res = self.host.stopProcess(task)
			
			if res:
				return {'message': f"Stopped process {task}"}
			else:
				return {'message': f"Problem stopping process {task}, is not running or does not exist."}
		
		elif value == "list":
			s = ""
			for item in self.host.threads:
				print(item)
				if self.host.config.data['processes'].get(item):
					s += f" [\x1b[32mON\x1b[0m] {self.host.threads[item]['object'].__class__.__module__}.{item}\n"
				else:
					s += f" [\x1b[31mOFF\x1b[0m] {self.host.threads[item]['object'].__class__.__module__}.{item}\n"
			return {'output':s[:-1]}
		
		else:
			return {'message': f"Invalid process command."}
		
class CfgGet(BaseCommand):
	"""
	This command returns a config variable.
	Format: get <variable>
	If variable input is empty, returns list of active variables.
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'get'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		if value == "":
			c = ""
			for item in self.host.config.data.keys():
				if type(self.host.config._get(item)) == dict:
					c += f"{item} = {json.dumps(self.host.config._get(item), indent=4)}\n"
				else:
					c += f"{item} = {self.host.config._get(item)} ({type(self.host.config._get(item))})\n"
			
			return {'output': c[:-1]}
		
		while " " in value:
			value = value.replace(" ", "_")
			
		#print(value)
		data = self.host.config._get(value)
		#print(data)
		if data != "":
			if type(data) == dict:
				data = json.dumps(data, indent=4)
			return {'output': f"{value} = {data}"}
		else:
			return {'message': "Config var isn't set."}

class Module(BaseCommand):
	"""
	Manages modules
	Format: module <command> <args>
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [self.message("module"), self.message("mods"), self.message("modules")]
		self.inter = True
		self.readme_cache = None
		
	def findBlock(self, data, block_name):
		start = -1
		end = -1
		
		for item in data:
			if item.startswith(f"{block_name}") and start == -1:
				#print(f"Found {item}")
				start = data.index(item)
				end = start
			if start != -1:
				#print(f"Checking if {item} is end")
				end += 1
				if item == "\n" or item == "" or item == " ":
					#print(f"Ended")
					
					#print(f"Ending: {start} - {end}")
					return data[start:end]
					
	def getReadme(self, module_name):
		if not self.readme_cache:
			print("Downloading readme")
			url = "https://raw.githubusercontent.com/codedthoughts/aosr-modules/master/README.md"
			self.readme_cache = requests.get(url).text
		else:
			pass
		data = self.readme_cache.split("\n")
		return self.findBlock(data, f"## {module_name}")	
	
	def onTrigger(self, value = ""):
		if value == "":
			value = "list"
			
		if value == "list":
			mods = []
			for item in self.host.command_cache:
				#print(item)
				if self.host.command_cache[item].__class__.__module__ not in mods:
					mods.append(self.host.command_cache[item].__class__.__module__)
			c = ""
			for item in mods:					
				if item in self.host.config._get('disabled_modules'):
					c += f" [\x1b[31mOFF\x1b[0m] "
				else:
					c += f" [\x1b[32mON\x1b[0m] "
				
				if item in self.host.core_modules:
					c += f"{self.host.formatting.Bold}{item}{self.host.reset_f}\n"
				else:
					c += f"{item}\n"
					
			return self.output(c[:-1])
		
		if value.startswith('enable '):
			value = value[7:]
			
			dl = self.host.config._get('disabled_modules')
			if value in dl:
				dl.remove(value)
				self.host.config._set('disabled_modules', dl)
				return self.message(f"Enabled {value} module.")
			else:
				return self.message(f"Module {value} isn't disabled")
			
		if value.startswith("disable "):
			value = value[8:]
			locked_vars = ['commands']
			if value in locked_vars:
				return self.message(f"Can't disable {value}, that is a core module.")
			
			passed = False
			for item in self.host.command_cache:
				if value == self.host.command_cache[item].__class__.__module__:
					passed = True
			
			if not passed:
				return self.message(f"Module {value} does not exist. Note that command names are case sensative references to their file name.")
			
			dl = self.host.config._get('disabled_modules')
			if value not in dl:
				dl.append(value)
				self.host.config._set('disabled_modules', dl)
				return self.message(f"Disabled {value} module.")
			else:
				return self.message(f"Command {value} already disabled")

		if value.startswith("find "):
			value = value[8:]
			
			req = requests.get(self.host.modules_manifest).text
			remote_manifest = json.loads(req)
			
			s = "\n"
			for item in remote_manifest:
				if item['name'].endswith(".py"):
					if value.lower() in item['name'].lower():
						s += f"{item['name']} : {self.host.colours.F_Blue}{item['download_url']}{self.host.reset_f}\n"
						r = self.getReadme(item['name'].split(".")[0])
						if r:
							r = '\n'.join(r)
							s += f"- {self.host.colours.F_Yellow}{r}{self.host.reset_f}"
			return self.output(s)
			
		if value == "find":			
			req = requests.get(self.host.modules_manifest).text
			remote_manifest = json.loads(req)
			s = "\n"
			for item in remote_manifest:
				if item['name'].endswith(".py"):
					s += f"{item['name']} : {self.host.colours.F_Blue}{item['download_url']}{self.host.reset_f}\n"
					r = self.getReadme(item['name'].split(".")[0])
					if r:
						r = '\n'.join(r)
						s += f"- {self.host.colours.F_Yellow}{r}{self.host.reset_f}"				
			return self.output(s)
		
		if value.startswith("install "):
			value = value[8:]
			
			req = requests.get(self.host.modules_manifest).text
			remote_manifest = json.loads(req)
			
			target = None
			for item in remote_manifest:
				if value.lower() in item['name'].lower():
					target = item['download_url']
			
			if not target:
				return self.message("Module not found.")
			
			if self.host.promptConfirm(f"Will try to download {value} from {target}"):
				self.host.getFile(target, 'ext/', options = '-N -q')
				return self.message(f"Installed {value}. Commands will be enabled after running 'refresh commands' or restarting the client.")
			else:
				return self.message("Cancelling.")

		if value.startswith("get "):
			value = value[4:]
					
			if self.host.promptConfirm(f"Will try to download {value} as an extension. (NOTE: This URL may not be secure or verified.)"):
				self.host.getFile(value, 'ext/', options = '-N -q')
				return self.message(f"Installed file.")
			else:
				return self.message("Cancelling.")
						
		if value.startswith("uninstall "):
			value = value[10:]
			if not value.startswith("ext."):
				value = f"ext.{value}"
			real_filepath = f"{self.host.scriptdir}ext/{value[4:]}.py"
			
			if value not in self.host.core_modules:
				if self.host.promptConfirm(f"Will try to permenantly delete {real_filepath}"):
					os.system(f"rm {real_filepath}")
					return self.message(f"Uninstalled {value}")
				else:
					return self.message("Cancelling.")
			else:
				return self.message(f"{value} is a core module, can't be uninstalled.")
class Disable(BaseCommand):
	"""
	Disables a command
	Format: disable <command>
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'disable'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		locked_vars = ['Help', 'Disable', 'Quit']
		if value in locked_vars:
			return self.message(f"Can't disable {value}, that is a core command.")
		
		passed = False
		for item in self.host.commands:
			if value == item[0]:
				passed = True
		
		if not passed:
			return self.message(f"Command {value} does not exist. Note that command names are case sensative references to their class name.")
		
		
		
		dl = self.host.config._get('disabled')
		if value not in dl:
			self.host.command_cache[value].onClose()
			dl.append(value)
			self.host.config._set('disabled', dl)
			return self.message(f"Disabled {value} command.")
		else:
			return self.message(f"Command {value} already disabled")
		
class Enable(BaseCommand):
	"""
	Re-enables a command
	Format: enable <command>
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'enable'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		dl = self.host.config._get('disabled')

		if value in dl:
			self.host.command_cache[value].onStart()
			dl.remove(value)
			self.host.config._set('disabled', dl)
			return self.message(f"Enabled {value} command.")
		else:
			return self.message(f"Command {value} already enabled")
	
class Aliases(BaseCommand):
	"""
	Allows defining of aliases for commands.
	Once defined, for example if KEY was set as 'me', in normal commands, if you enter the alias character (default %) then me, then that will be replaced with the message set.
	Format: alias <key> <new message>
	If no key or message given, will output all current aliases.
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'alias'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		aliases = self.host.config._get('aliases', {})
		if value == "":
			if len(aliases) == 0:
				return self.message("No aliases set.")
			
			s = ""
			for alias in aliases:
				s += f"{alias} = {aliases[alias]}\n"
			
			return self.output(s[:-1])
			
		key = value.split()[0]
		msg = value.split()[1:]
		msg = ' '.join(msg)
		aliases[key] = msg
		self.host.config._set('aliases', aliases)
		return self.message("Alias set.")
	
class Unalias(BaseCommand):
	"""
	Removes an alias
	Format: unalias <key>
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'unalias'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		aliases = self.host.config._get('aliases', {})
		del aliases[value]
		self.host.config._set('aliases', aliases)
		return self.message("Alias set.")
				
class CfgUnSet(BaseCommand):
	"""
	Deletes a command variable.
	Format: unset <key>
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'unset'}]
		self.inter = True
		
	def onTrigger(self, value = ""):
		locked_vars = ['tts', 'username', 'tasks', 'events', 'disabled', 'skip_prompts']
		if value in locked_vars:
			return self.message(f"Can't delete {value}, that is a core variable.")
		try:
			if self.host.promptConfirm(f"Are you sure you want to delete config var {value}?"):
				del self.host.config.data[value]
				self.host.config.save()
				return {'message': f'Okay, deleted config variable {value}'}
			else:
				return self.message("Okay, cancelled.")
		except:
			return {'message': f'Error deleting that.'}

class CfgSet(BaseCommand):
	"""
	Sets a command variable.
	Format: set <key> to <value>
	Everything before "to" will be converted to the config key, everything after becomes its value.
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'set'}]
		self.inter = True
		self.alias = "set"
		
	def onTrigger(self, value = ""):
		#print(value)
		#print(self.host.scriptdir)
		
		if not " to " in value:
			return {'message': f"Bad formatting, format is `set key to value`"}
		
		key = value.split(" to ")[0]
		key = key.strip()
		while " " in key:
			key = key.replace(" ", "_")
			
		locked_vars = ['tasks', 'events', 'disabled']
		if key in locked_vars:
			return self.message(f"Can't edit {key}, that variable can only be modified through the relevant command.")
		
		val = value.split(" to ")[1:]
		val = ' '.join(val)
		val = val.strip()
		_val = val
		
		if _val.lower() == "true":
			val = True
		elif _val.lower() == "false":
			val = False
		elif _val.isdigit():
			val = int(val)
			
		if self.host.config._get(key):
			print(f"Old: {self.host.config._get(key)}")
			if self.host.promptConfirm(f"Are you sure you want to overwrite config var {key}?"):
				self.host.config._set(key, val)
				return {'message': f'Okay, key {key} set to {val}'}
			else:
				return self.message("Alright, cancelled.")
		else:
			self.host.config._set(key, val)
			return {'message': f'Okay, key {key} set to {val}'}

class Refresh(BaseCommand):
	"""
	Executes defined terminal command
	Format: run <code>
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'refresh commands', 'check': 90}]
		
	def onTrigger(self, value = ""):
		self.host.updateCommands(self.host)

class Logs(BaseCommand):
	"""
	Log manager
	
		log - Shows all log groups
		log <group> - Shows logs in specific group
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'logs'}, {'message':'log'}]
		self.inter = True

	def onTrigger(self, value = ""):
		if value == "":
			s = ""
			for item in list(self.host.logs.data.keys()):
				if len(self.host.logs._get(item)) > 0:
					s += f" {self.host.formatting.Bold}{item}{self.host.reset_f} [{len(self.host.logs._get(item))}]\n"
			
			return self.output(s[:-1])
		
		data = self.host.logs._get(value, [])
		if len(data) == 0:
			return self.message(f"No logs for {value}")
		
		s = f"-- Log for {self.host.formatting.Bold}{value}{self.host.reset_f} ({len(data)} items) --\n"
		
		for item in data:
			s += f"{self.host.formatting.Bold}{item['timestamp']}{self.host.reset_f}: {item['message']}\n"
		
		return self.output(s[:-1])
	
class PurgeLogs(BaseCommand):
	"""
	Log manager
	
		log - Shows all log groups
		log <group> - Shows logs in specific group
		
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'purge log'}]
		self.inter = True

	def onTrigger(self, value = ""):
		if value == "":
			return self.message("A log key is needed.")
		
		data = self.host.logs._get(value, [])
		if len(data) == 0:
			return self.message(f"No logs for {value}")
		
		self.host.logs._set(value, [])
		return self.message(f"Purged log {value}")
	
class Bash(BaseCommand):
	"""
	Executes defined terminal command
	Format: run <code>
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'bash'}, {'message':'run'}, {'message':'$'}]
		self.inter = True
		self.alias = "execute"
		
	def onHeld(self, value):
		try:
			os.system(f'{value}&')
			return {'message': f"Executing bash commands."}
		except Exception as e:
			return {'message': e}
		
	def onTrigger(self, value = ""):
		if not value:
			return self.hold("Run what?")
		
		try:
			os.system(f'{value}&')	
			return {'message': f"Executing bash commands."}
		except Exception as e:
			return {'message': e}

class CrEvent(BaseCommand):
	"""
	Modifies event data
	event <key> <type ['eval', 'message']> <data>
	
	No value defined lists all events.
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("event")
		self.inter = True
	
	def onTrigger(self, value = ""):
		data = self.host.config._get('events', {})
		if value == "":
			if len(data) == 0:
				return self.message("No events defined.")
			s = ""
			for item in data:
				s += f"{data[item]['type']} - \x1b[33m{item}\x1b[0m\n{data[item]['data']}\n\n"
			
			return self.output(s[:-2])
		
		if value.startswith("-del"):
			parsed = value.split(" ")[1]
			try:
				test = data[parsed]
				if self.host.promptConfirm(f"Are you sure you want to delete event {parsed}?"):
					del data[parsed]
					self.host.config._set('events', data)
					return self.message("Deleted event.")
			except KeyError:
				return self.message("Event does not exist.")
			
		if value.startswith("-run"):
			parsed = value.split(" ")[1]
			
			return self.host.runEvent(parsed) 
		
		key = value.split(" ")[0]
		event_type = value.split(" ")[1]
		event_data = value.split(" ")[2:]
		event_data = ' '.join(event_data)
		
		valid_types = ['message', 'eval', 'output', 'terminal']
		if event_type not in valid_types:
			return self.message(f"{event_type} is an invalid type.")
		
		try:
			test = data[key]
			if self.host.promptConfirm(f"Are you sure you want to overwrite event {key}?"):
				data[key] = {'type': event_type, 'data':event_data}
				self.host.config._set('events', data)
				return self.message(f"Modified event {key}.")
			else:
				return self.message("Cancelled process.")
		except KeyError:	
			data[key] = {'type': event_type, 'data': event_data}
			self.host.config._set('events', data)
			return self.message(f"Created event {key}.")
	
class Eval(BaseCommand):
	"""
	Evaluates arbitrary python code.
	Format: eval <code>
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [self.message("evaluate"), self.message("eval")]
		self.inter = True
	
	def onHeld(self, value):
		try:
			eval(value)
		except Exception as e:
			return {'message': f"Value failed to evaluate for the following reason: {e}"}
		
	def onTrigger(self, value = ""):
		if not value:
			return self.hold("Evaluate what?")
		
		try:
			eval(value)
		except Exception as e:
			return {'message': f"Value failed to evaluate for the following reason: {e}"}
		
class Updating(BaseCommand):
	"""
	Handles manual and automatic updating.
	[BASE]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [self.message("update")]
		self.inter = True
		
		if self.host.config._get('update_check_on_startup'):
			self.host.config._set('has_updates', self.ucheck()['updates'])
			
	def ucheck(self):
		s = ""
		updates = False
		with open(self.host.scriptdir+'manifest.json') as f:
			local_manifest = json.loads(f.read())
							
			req = requests.get(self.host.master_manifest).text
			remote_manifest = json.loads(req)
			
			for item in remote_manifest['files']:
				rem_mod = remote_manifest['files'].get(item)
				local_mod = local_manifest['files'].get(item)
				if rem_mod and local_mod:
					if rem_mod['version'] == local_mod['version']:
						s += f"{item} OK\n"
					else:
						s += f"{item} outdated. LOCAL: {local_mod['version']} - REMOTE: {rem_mod['version']}\n"
						s += f"Consider updating with `update check` or manually downloading the file at {rem_mod['url']}\n"
						updates = True
				else:
					s += f"{item} missing from local manifest."
					
		return {'updates': updates, 'output': s[:-1]}
	
	def onTrigger(self, value = ""):
		if not value:
			return self.message("Needs an operation, example: update check, update get")
		
		if value == "check":
			return self.output(self.ucheck()['output'])
					
		elif value.startswith("get "):
			value = value[4:]
			print("Getting "+value)
			req = requests.get(self.host.master_manifest).text
			remote_manifest = json.loads(req)
			
			with open(self.host.scriptdir+'manifest.json') as f:
				local_manifest = json.loads(f.read())

				for item in remote_manifest['files']:
					print(item)
					print(value)
					if value == item:
						print("Ready to update.")
						if local_manifest['files'][item]['version'] == remote_manifest['files'][item]['version']:
							return self.message("File is already up to date.")
						
						if "/ext/" in remote_manifest['files'][item]['url']:
							self.host.getFile(remote_manifest['files'][item]['url'], 'ext/', options = '-N -q')
							
						elif "/processes/" in remote_manifest['files'][item]['url']:
							self.host.getFile(remote_manifest['files'][item]['url'], 'processes/', options = '-N -q')
							
						else:
							self.host.getFile(remote_manifest['files'][item]['url'], options = '-N -q')
						
						local_manifest['files'][item]['version'] = remote_manifest['files'][item]['version']
						
					with open(self.host.scriptdir+'manifest.json', 'w') as fp:
						json.dump(local_manifest, fp, indent=4)
						
					return self.message("Finished updating.")
					
			return self.message(f"Failed to update; {value} invalid target.")
		
		elif value.startswith("get"):
			req = requests.get(self.host.master_manifest).text
			remote_manifest = json.loads(req)
			
			with open(self.host.scriptdir+'manifest.json') as f:
				local_manifest = json.loads(f.read())

				for item in remote_manifest['files']:
					rem_mod = remote_manifest['files'].get(item)
					local_mod = local_manifest['files'].get(item)
					if local_mod and rem_mod:
						if local_mod['version'] == rem_mod['version'] and not self.host.config._get('force_global_update'):
							print("Skipping "+item)
						
						else:
							if "/ext/" in rem_mod['url']:
								self.host.getFile(rem_mod['url'], 'ext/', options = '-N -q')
								
							elif "/processes/" in rem_mod['url']:
								self.host.getFile(rem_mod['url'], 'processes/', options = '-N -q')
								
							else:
								self.host.getFile(rem_mod['url'], options = '-N -q')
							if not local_mod:
								local_manifest['files'][item] = {'url':rem_mod['url'], 'version': rem_mod['version']}
							else:
								local_manifest['files'][item]['version'] = remote_manifest['files'][item]['version']
							
					else:
						print(f"Desync found in {item}")
						if "/ext/" in rem_mod['url']:
							self.host.getFile(rem_mod['url'], 'ext/', options = '-N -q')
							
						elif "/processes/" in rem_mod['url']:
							self.host.getFile(rem_mod['url'], 'processes/', options = '-N -q')
							
						else:
							self.host.getFile(rem_mod['url'], options = '-N -q')
						
						if not local_mod:
							local_manifest['files'][item] = {'url':rem_mod['url'], 'version': rem_mod['version']}
						else:
							local_manifest['files'][item]['version'] = remote_manifest['files'][item]['version']
							
			with open(self.host.scriptdir+'manifest.json', 'w') as fp:
				json.dump(local_manifest, fp, indent=4)
				
			return self.message("Finished updating.")
