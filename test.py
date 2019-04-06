import os
import importlib
import inspect
import sys
import art
import memory
import arrow
from Color import *

class CommandInfo:
	def __init__(self):
		self.scriptdir = os.path.dirname(os.path.abspath(__file__))+"/"
		self.config = None
		self.commands = []

def printf(text, *, tag="", ts=True):
	if ts:
		time = now()
	else:
		time = ""
	if tag == "say":
		print(f"{time} [ {Color.F_Blue}SAY{Base.END} ] {text}")
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
	printf(text, tag="say")
	text = text.replace('"', "'") #Preventing the console command breaking if the user inputs quote marks, since the .system will think THEIR quote marks are ending the ones this script uses, and means any other text in the input will be, at best ignored, at worst flite will try and translate them in to command args, which could result in random file dumping and other weird interactions
	os.system(f'padsp flite -voice file://{gcinfo.scriptdir}cmu_us_clb.flitevox -t "{text}" &')	
	
def process_commands(phrase):
	for item in gcinfo.commands:
		print(item[1])
		if item[1]().check(phrase):
			return_data = item[1]().trigger()
			#print(return_data)
			if return_data:
				try:
					if return_data['message']:
						say(return_data['message'])
				except KeyError:
					pass
				
				try:
					if return_data['code'] == "quit":
						quit()
				except KeyError:
					pass
def run_cli():
	printf("Loading Athena", tag="info")
	#user = touchConfig('core', 'username', os.environ.get('USER'))
	user = gcinfo.config.get('username')
	say(f"What do you need, {user}?")
	listening = True

	while True:
		phrase = input("(> ")
		printf(f"Captured: {phrase}", tag="info")
		resp = process_commands(phrase)
	
def run():
	global gcinfo
	gcinfo = CommandInfo()
	gcinfo.config = memory.Memory(logging=True)
	commandsf = []
	for file in os.listdir(gcinfo.scriptdir+"ext/"):
		filename = os.fsdecode(file)
		if filename.endswith(".py"):
			modname = filename.split(".")[0]
			print(modname)
			importlib.import_module("ext."+modname)
			clsmembers = inspect.getmembers(sys.modules["ext."+modname], inspect.isclass)
			#print(clsmembers)
			commandsf += clsmembers
	gcinfo.commands = commandsf		
	print(commandsf)
	
	run_cli()
		
run()
