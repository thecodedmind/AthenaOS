#!/usr/bin/env python3

import os
import subprocess
import importlib
import inspect
import sys
import art
import memory
import arrow
from Color import *
import multiprocessing
from time import sleep
from ext.commands import BaseCommand
from processes.processes import AOSProcess
import humanfriendly
from humanfriendly import AutomaticSpinner
import readline

class CommandInfo:
	def __init__(self):
		self.scriptdir = os.path.dirname(os.path.realpath(__file__))+"/"
		printf(f"Script dir: {self.scriptdir}", tag='info')
		self.config = None
		self.commands = []
		self.command_cache = {}
		self.say = say
		self.printf = printf
		self.updateProcesses = initCacheProcesses
		self.updateCommands = initCacheCommands
		self.processCommands = process_commands
		self.threads = {}
		self.master_host = "https://github.com/codedthoughts/AthenaOS/raw/master/"
		self.master_manifest = self.master_host+"/manifest.json"
		self.modules_manifest = "https://github.com/codedthoughts/aosr-modules/raw/master/manifest.json"
		self.formatting = Formatting
		self.colours = Color
		self.reset_f = Formatting.Reset
		self.core_modules = ['ext.commands', 'ext.kext']
		self.logs = None
		
	def logAction(self, group:str, message:str):
		ts = arrow.now().format('YYYY-MM-DD HH:mm:ss')
		
		data = {
			'message': str(message),
			'timestamp': ts
		}
		g = self.logs._get(str(group), [])
		g.append(data)
		self.logs._set(str(group), g)
		
	def terminal(self, command):
		res = subprocess.run(command.split(" "), stdout=subprocess.PIPE)
		return str(res.stdout,"latin-1")	
	
	def humanizeList(self, ls):
		return humanfriendly.text.concatenate(ls)
	
	def getFile(self, url, save_to = "", *, options = ""):
		out_dir = self.scriptdir+save_to
		os.system(f'wget {url} -P {out_dir} {options}&')	
		
	def promptConfirm(self, message):
		if self.config._get('skip_prompts'):
			return True
		
		if humanfriendly.prompts.prompt_for_confirmation(message):
			return True
		else:
			return False
	
	def runEvent(self, event):
		try:
			data = self.config._get('events')[event]
			if data['type'] == 'eval':
				eval(data['data'])
			elif data['type'] == "message" or data['type'] == 'output':
				return {data['type']: data['data']}
			elif data['type'] == "terminal":
				t = self.terminal(data['data'])
				return {'output': t}
		except KeyError:
			return {'message': "Invalid event data."}
		
	def startProcess(self, task):
		if self.config.data['processes'][task]:
			return False
		
		self.threads[task]['object'].start()
		return True
	
	def stopProcess(self, task):
		if not self.config.data['processes'][task]:
			return False
		
		self.threads[task]['object'].stop()
		return True
			
def printf(text, *, tag="", ts=True):
	if ts:
		time = now()
	else:
		time = ""
	if tag == "say":
		print(f"{time} [ {Color.F_Blue}SAY{Base.END} ] {text}")
	elif tag == "say-notts":
		print(f"{time} [ {Color.F_Green}QUIET SAY{Base.END} ] {text}")
	elif tag == "output":
		print(f"{time} [ {Color.F_LightCyan}OUTPUT START{Base.END} ]\n{text}\n[ {Color.F_LightCyan}OUTPUT END{Base.END} ]")
	elif tag == "error":
		print(f"{time} [ {Color.F_Red}ERROR{Base.END} ] {Formatting.Bold}{text}{Formatting.Reset_Bold}")
	elif tag == "info":
		print(f"{time} [ {Color.F_LightGray}INFO{Base.END} ] {text}")
	else:
		print(f"{time} | {text}")

def now():
	h = arrow.now().hour
	m = arrow.now().minute
	s = arrow.now().second
	if h < 10:
		h = f"0{h}"
	if m < 10:
		m = f"0{m}"
	if s < 10:
		s = f"0{s}"
	return f"{h}:{m}:{s} "	

def say(text):
	gcinfo.logAction('say', text)
	if not gcinfo.config._get('tts'):
		printf(text, tag="say-notts")
		return
	else:
		printf(text, tag="say")
	
	text = text.replace('"', "'") #Preventing the console command breaking if the user inputs quote marks, since the .system will think THEIR quote marks are ending the ones this script uses, and means any other text in the input will be, at best ignored, at worst flite will try and translate them in to command args, which could result in random file dumping and other weird interactions
	os.system(f'padsp flite -voice file://{gcinfo.scriptdir}cmu_us_clb.flitevox -t "{text}" &')	

def parseResult(command, phrase):
	#print(phrase)
	for item in command.phrases:
		#print(item)
		if phrase.startswith(item['message']):
			length = len(item['message'])
			return phrase[length:].strip()#phrase.replace(item['message'], "").strip()

def checkAliases(message):
	aliases = gcinfo.config._get('aliases', {})
	ach = gcinfo.config._get('alias_character', "%")
	if len(aliases) == 0:
		return message
	
	for item in aliases:
		if f"{ach}{item}" in message:
			message = message.replace(f"{ach}{item}", aliases[item])
			
	return message

def process_commands(phrase):
	for item in gcinfo.commands:
		if issubclass(item[1], BaseCommand):
			inst = gcinfo.command_cache[item[0]]
			if inst.check(phrase):
				if inst.inter:
					#print(item)
					value = parseResult(inst, phrase)
					value = checkAliases(value)
					#print(f"Got value {value}")
					return_data = inst.onTrigger(value)
				else:
					try:
						return_data = inst.onTrigger()
					except TypeError:
						return_data = inst.onTrigger("")
				#print(return_data)
				if return_data:
					handleReturnData(return_data)

def handleReturnData(return_data):
	if return_data.get('message'):
		say(return_data['message'])

	if return_data.get('output'):
		gcinfo.logAction('output', return_data['output'])
		printf(return_data['output'], tag='output')
		
	if return_data.get('code') == "hold":
		response = input("? (> ")
				   
		response = return_data.get('held').onHeld(response)
		if response:
			handleReturnData(response)
			
	if return_data.get('code') == "quit":
		gcinfo.logAction('system', "Quit by command.")
		quit()
	
def run_cli():
	printf("Loading Athena", tag="info")
	#user = touchConfig('core', 'username', os.environ.get('USER'))
	user = gcinfo.config._get('username')
	if user == "":
		gcinfo.config._set('username', os.environ.get('USER'))
		user = os.environ.get('USER')
		
	gcinfo.logAction('system', "System startup.")	
	
	say(f"What do you need, {user}?")

	while True:
		phrase = input("(> ")
		resp = process_commands(phrase)
		#printf(f"Captured: {phrase}", tag="info")
		

def initCreateCore():
	printf("Creating core...", tag='info')
	gcinfo = CommandInfo()
	gcinfo.config = memory.Memory(path=gcinfo.scriptdir, logging=True)
	gcinfo.logs = memory.Memory(path=gcinfo.scriptdir+"logs.json", logging=True)
	return gcinfo

def initCacheProcesses(gcinfo):
	printf("Getting background processes...", tag='info')
	tasks = gcinfo.config._get('processes')
	if not tasks:
		gcinfo.config._set('processes', {})
		
	for file in os.listdir(gcinfo.scriptdir+"processes/"):
		filename = os.fsdecode(file)
		if filename.endswith(".py"):
			modname = filename.split(".")[0]
			printf(f"Loading process module: {modname}", tag='info')
			importlib.import_module("processes."+modname)
			clsmembers = inspect.getmembers(sys.modules["processes."+modname], inspect.isclass)
			for item in clsmembers:
				try:
					if issubclass(item[1], AOSProcess) and item[0] != "AOSProcess":
						printf(f"Validated {item}", tag='info')
						item[1](gcinfo)
				except Exception as e:
					pass
		
def initCacheCommands(gcinfo):
	gcinfo.commands = {}
	gcinfo.command_cache = {}
	commandsf = []
	
	off_modules = gcinfo.config._get('disabled_modules')
	if not off_modules:
		gcinfo.config._set('disabled_modules', [])
		
	off_commands = gcinfo.config._get('disabled')
	if not off_commands:
		gcinfo.config._set('disabled', [])
		
	printf("Getting Command modules...", tag='info')
	for file in os.listdir(gcinfo.scriptdir+"ext/"):
		filename = os.fsdecode(file)
		if filename.endswith(".py"):
			modname = filename.split(".")[0]
			if f"ext.{modname}" not in off_modules:
				printf(f"Loading command module: {modname}", tag='info')
				importlib.import_module("ext."+modname)
				clsmembers = inspect.getmembers(sys.modules["ext."+modname], inspect.isclass)
				#print(clsmembers)
				commandsf += clsmembers
			else:
				print(f"Not loading {modname}")
	
	invalid_classes = []
	for item in commandsf:
		if issubclass(item[1], BaseCommand):
			printf(f"Validated {item}", tag='info')
			gcinfo.command_cache[item[0]] = item[1](gcinfo)
			gcinfo.command_cache[item[0]].onStart()
		else:
			invalid_classes.append(item)
	
	for item in invalid_classes:
		#printf(f"Invalidating {item}")
		commandsf.remove(item)	
	
	dis = gcinfo.config._get('disabled')
	if not dis:
		gcinfo.config._set('disabled', [])
		dis = []
		
	gcinfo.commands = commandsf	
	
def run():
	global gcinfo
	with AutomaticSpinner(label="Loading Athena..."):
		gcinfo = initCreateCore()
		initCacheProcesses(gcinfo)
		initCacheCommands(gcinfo)
	try:
		run_cli()
	except KeyboardInterrupt:
		print("Closing.")
	except Exception as e:
		print(e)
		run_cli()
run()
