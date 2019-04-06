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
		self.phrases = {}
		self.inter = False
		self.host = host
		self.alias = type(self).__name__
		self.hidden = False
		self.disabled = False
		
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
			return False
		
		for item in self.phrases:
			if not self.inter:
				if fuzz.ratio(check_message.lower(), item['message'].lower()) >= item['check']:
					return True
			else:
				if check_message.lower().startswith(item['message'].lower()):
					return True
	
	def onTrigger(self, value = ""):
		self.onTrigger(self, value)
	
	def hold(self, message):
		return {'message': message, 'code': 'hold', 'held': self}
	
	def onHold(self, value):
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
		#self.alias = "hold"
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
		
class CommandsList(BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'commands', 'check': 95}]
		
	def onTrigger(self):
		c = ""
		for item in self.host.commands:
			if not self.host.command_cache[item[0]].hidden and item[0].lower() != "basecommand":
				if item[0] in self.host.config._get('disabled'):
					c += f"[\x1b[31mOFF\x1b[0m] {self.host.command_cache[item[0]].__class__.__module__}.{item[0]}\n"
				else:
					c += f"[\x1b[32mON\x1b[0m] {self.host.command_cache[item[0]].__class__.__module__}.{item[0]}\n"
		
		return self.output(c)
			
class Help(BaseCommand):
	"""
	This is a help.
	Format: help <command>
	Searches by the command class name and its alias variable.
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
			if inst.check(value):#if value.lower() == item[0].lower() or value.lower() == inst.alias:
				return {'output': inst.getHelp()}
			
	def onHeld(self, value):
		if value == "cancel" or value == "":
			return {'message': "Cancelling help menu."}
		
		for item in self.host.commands:
			inst = item[1](self.host)
			if inst.check(value):#if value.lower() == item[0].lower() or value.lower() == inst.alias:
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
			return {'output':humanfriendly.text.concatenate(self.host.process_cache.keys())}
		
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
		self.alias = "get"
		
	def onTrigger(self, value = ""):
		if value == "":
			c = ""
			for item in self.host.config.data.keys():
				c += f"{item} = {self.host.config._get(item)} ({type(self.host.config._get(item))})\n"
			
			return {'output': c[:-1]}
		
		while " " in value:
			value = value.replace(" ", "_")
			
		#print(value)
		data = self.host.config._get(value)
		if data != "":
			return {'output': data}
		else:
			return {'message': "Config var isn't set."}

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
			dl.remove(value)
			self.host.config._set('disabled', dl)
			return self.message(f"Enabled {value} command.")
		else:
			return self.message(f"Command {value} already enabled")
		
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
		
		if not "to" in value:
			return {'message': f"Bad formatting, format is `set key to value`"}
		
		key = value.split("to")[0]
		key = key.strip()
		while " " in key:
			key = key.replace(" ", "_")
			
		locked_vars = ['tasks', 'events', 'disabled']
		if key in locked_vars:
			return self.message(f"Can't edit {key}, that variable can only be modified through the relevant command.")
		
		val = value.split("to")[1:]
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
		self.phrases = [self.message("event"), self.message("mod event")]
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
		
		valid_types = ['message', 'eval', 'output']
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
		with open('manifest.json') as f:
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
					
		return {'updates': updates, 'output': s}
	
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
			
			with open('manifest.json') as f:
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
						with open('manifest.json', 'w') as fp:
							json.dump(local_manifest, fp, indent=4)
						return self.message("Finished updating.")
					
			return self.message(f"Failed to update; {value} invalid target.")
		
		elif value.startswith("get"):
			req = requests.get(self.host.master_manifest).text
			remote_manifest = json.loads(req)
			
			with open('manifest.json') as f:
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
							
				with open('manifest.json', 'w') as fp:
					json.dump(local_manifest, fp, indent=4)
					
				return self.message("Finished updating.")
