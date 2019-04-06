#!/usr/bin/env python3

import os
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
import humanfriendly
from humanfriendly import AutomaticSpinner

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
		self.threads = {}
		self.process_cache = {}
		self.master_host = "https://github.com/codedthoughts/AthenaOS/raw/master/"
		self.master_manifest = self.master_host+"/manifest.json"

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
		except KeyError:
			return {'message': "Invalid event data."}
		
	def runProcess(self, task, name):
		printf("Running process thread...", tag='info')
		printf(task, tag='info')
		thread = multiprocessing.Process(target=task, args=([self]))
		self.threads[name] = thread
		print(self.threads)
		thread.daemon = True
		thread.start()
	
	def startProcess(self, task):
		printf("Starting process thread...", tag='info')
		printf(task)
		printf(self.config.data['processes'][task])
		if self.config.data['processes'][task]:
			return False
		
		taskobject = self.process_cache[task]
		self.config.data['processes'][task] = True
		self.config.save()
		thread = multiprocessing.Process(target=taskobject, args=([self]))
		self.threads[task] = thread
		thread.daemon = True
		thread.start()
		return True
	
	def stopProcess(self, task):
		print(self.threads)
		printf("Stopping process thread...", tag='info')
		printf(task)
		try:
			self.threads[task].terminate()
			del self.threads[task]
			self.config.data['processes'][task] = False
			self.config.save()
			return True
		except KeyError:
			return False
			
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
	if not gcinfo.config._get('tts'):
		printf(text, tag="say-notts")
		return
	else:
		printf(text, tag="say")
	
	text = text.replace('"', "'") #Preventing the console command breaking if the user inputs quote marks, since the .system will think THEIR quote marks are ending the ones this script uses, and means any other text in the input will be, at best ignored, at worst flite will try and translate them in to command args, which could result in random file dumping and other weird interactions
	os.system(f'padsp flite -voice file://{gcinfo.scriptdir}cmu_us_clb.flitevox -t "{text}" &')	

def parseResult(command, phrase):
	for item in command.phrases:
		if item['message'] in phrase:
			return phrase.replace(item['message'], "").strip()
		
def process_commands(phrase):
	for item in gcinfo.commands:
		if issubclass(item[1], BaseCommand):
			inst = gcinfo.command_cache[item[0]]#item[1](gcinfo)
			#print(inst)
			#print(inst.inter)
			if inst.check(phrase):
				if inst.inter:
					value = parseResult(inst, phrase)
					#print(f"Got value {value}")
					return_data = inst.onTrigger(value)
				else:
					return_data = inst.onTrigger()
					
				#print(return_data)
				if return_data:
					handleReturnData(return_data)

def handleReturnData(return_data):
	if return_data.get('message'):
		say(return_data['message'])

	if return_data.get('output'):
		printf(return_data['output'], tag='output')
		
	if return_data.get('code') == "hold":
		response = input("? (> ")
				   
		response = return_data.get('held').onHeld(response)
		if response:
			handleReturnData(response)
			
	if return_data.get('code') == "quit":
		quit()
		
def run_cli():
	printf("Loading Athena", tag="info")
	#user = touchConfig('core', 'username', os.environ.get('USER'))
	user = gcinfo.config._get('username')
	if user == "":
		gcinfo.config._set('username', os.environ.get('USER'))
		user = os.environ.get('USER')
		
	say(f"What do you need, {user}?")
	listening = True

	while True:
		phrase = input("(> ")
		#printf(f"Captured: {phrase}", tag="info")
		resp = process_commands(phrase)

def initCreateCore():
	printf("Creating core...", tag='info')
	gcinfo = CommandInfo()
	gcinfo.config = memory.Memory(path=gcinfo.scriptdir, logging=True)
	return gcinfo

def initCacheProcesses(gcinfo):
	printf("Loading background processes...", tag='info')
	tasks = gcinfo.config._get('processes', {})
	changes = False
	for file in os.listdir(gcinfo.scriptdir+"processes/"):
		filename = os.fsdecode(file)
		if filename.endswith(".py"):
			modname = filename.split(".")[0]
			printf(f"Loading task module: {modname}", tag='info')
			importlib.import_module("processes."+modname)
			clsmembers = inspect.getmembers(sys.modules["processes."+modname], inspect.isfunction)
			for item in clsmembers:
				#print(inspect.getfullargspec(item[1]))
				try:
					if inspect.getfullargspec(item[1]).args[0] == 'event':
						printf(f"{item} found", tag='info')
						gcinfo.process_cache[item[0]] = item[1]
						if item[0] not in tasks.keys():
							printf(f"Adding {item[0]} to processes.", tag='info')
							tasks[item[0]] = False
							changes = True
						else:
							#printf(f"Running {tasks[item[0]]}", tag='info')
							if tasks[item[0]]:
								gcinfo.runProcess(item[1], item[0])
				except Exception as e:
					pass#print(e)
	if changes:
		printf("Updating processes config, new process have been added...", tag='info')
		gcinfo.config._set('processes', tasks)	
		
def initCacheCommands(gcinfo):
	commandsf = []
	printf("Getting Command modules...", tag='info')
	for file in os.listdir(gcinfo.scriptdir+"ext/"):
		filename = os.fsdecode(file)
		if filename.endswith(".py"):
			modname = filename.split(".")[0]
			printf(f"Loading command module: {modname}", tag='info')
			importlib.import_module("ext."+modname)
			clsmembers = inspect.getmembers(sys.modules["ext."+modname], inspect.isclass)
			#print(clsmembers)
			commandsf += clsmembers
	
	
	invalid_classes = []
	for item in commandsf:
		if issubclass(item[1], BaseCommand):
			printf(f"Validated {item}", tag='info')
			gcinfo.command_cache[item[0]] = item[1](gcinfo)
		else:
			invalid_classes.append(item)
	
	for item in invalid_classes:
		printf(f"Invalidating {item}")
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
	run_cli()
		
run()
