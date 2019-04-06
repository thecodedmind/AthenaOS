import arrow
import os
from Color import *
import asyncio
import json
import sys
from textblob import TextBlob, Word
from textblob.exceptions import NotTranslated, TranslatorError

import contextlib
scriptdir = os.path.dirname(os.path.abspath(__file__))+"/"
current_command = ""

#commands = [testcommand(), testheldcommand(1)]

class command:
	def __init__(self, mode=0, trigger_phrase=""): 
		#Mode 0 is one-line command, Mode 1 is command then wait for arg response from user
		self.mode = mode
	
	def trigger(self): #always the entry point for triggering
		pass
	
	def held_trigger(self): #the waited response trigger
		pass
		
class testcommand(command):
	def trigger(self):
		say("Trigger standard test.")
		
class testholdcommand(command):
	def trigger(self):
		say("Trigger held test. wait for reply.")		
	
	def held_trigger(self):
		say("Got hold.")
		
def getConfig(parent="", key="", *, filename="config"):
	with open(scriptdir+filename+".json") as f:
		data = json.load(f)
		
		if parent == "" and key == "":
			return data
		else:
			try:
				if key == "":
					return data[parent]
				else:
					return data[parent][key]
			except:
				return "NO_CONFIG_KEY"

def setConfig(parent:str, key:str, value, *, filename="config", logging=False):
	if logging:
		AddLog(f"{parent} : {key} : {value}")
	data = getConfig(filename=filename)
	try:
		data[parent][key] = value
	except:
		data[parent] = {}
		data[parent][key] = value
	with open(scriptdir+filename+'.json', "w") as s:
		json.dump(data, s, indent=4)

def dumpConfig(data, filename="config"):
	with open(scriptdir+filename+'.json', "w") as s:
		json.dump(data, s, indent=4)

def touchConfig(parent:str, key:str, default, *, filename="config"):
	with open(scriptdir+filename+".json") as f:
		data = json.load(f)
		try:
			return data[parent][key]
		except:
			setConfig(parent, key, default, filename=filename)
			return default
	
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
		
def say(text):
	printf(text, tag="say")
	text = text.replace('"', "'") #Preventing the console command breaking if the user inputs quote marks, since the .system will think THEIR quote marks are ending the ones this script uses, and means any other text in the input will be, at best ignored, at worst flite will try and translate them in to command args, which could result in random file dumping and other weird interactions
	os.system(f'padsp flite -voice file://{scriptdir}cmu_us_clb.flitevox -t "{text}" &')	

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

async def process_commands(phrase, single=False, quiet=False):	
	global listening, current_command
	with contextlib.suppress(AttributeError):
		printf(phrase.segments(detailed=True), tag="info")
		
	if str(phrase) == "exit" or str(phrase) == "quit":
		if current_command == "":
			printf(f"Listener closed.", tag="info")
			msg = "Goodbye."
			say(msg)
			return {'break':True, 'msg':msg}
		else:
			
			msg = f"Cancelling {current_command} command.."
			say(msg)
			current_command = ""
			return {'break':False, 'msg':msg}	
	else:
		if not current_command:
			if "who am i" in str(phrase).lower():
				user = touchConfig('core', 'username', os.environ.get('USER'))	
				msg = f"You are {user}."
				say(msg)
				return {'break':single, 'msg':msg}
			
			if str(phrase).startswith("define"):
				rlcm = str(phrase).split(" ")
				rlcm.pop(0)
				phrase = ' '.join(rlcm)
				blob = Word(phrase)
				defs = blob.definitions
				s = ""
				if len(defs) > 0:
					for item in defs:
						s += item+"\n"
					msg = s
					say(msg)
					return {'break':single, 'msg':msg}
				else:
					msg = "No results found."
					say(msg)
					return {'break':single, 'msg':msg}
			
			if str(phrase).startswith("repeat") or str(phrase).startswith("say"):
				rlcm = str(phrase).split(" ")
				rlcm.pop(0)
				phrase = ' '.join(rlcm)
				msg = str(phrase)
				say(msg)
				return {'break':single, 'msg':msg}	
			
			if str(phrase).startswith("calc") or str(phrase).startswith("eval"):
				rlcm = str(phrase).split(" ")
				rlcm.pop(0)
				phrase = ' '.join(rlcm)
				msg = eval(str(phrase))
				say(f"Calculating. {msg}")
				return {'break':single, 'msg':msg}	
			
			if "set my name" in str(phrase):
				current_command = "setname"
				msg = "What should I call you?"
				say(msg)
				return {'break':False, 'msg':msg}
			
			elif str(phrase).startswith("call me"):
				phrase = str(phrase).replace("call me ", '')
				msg = f"Okay, I'll call you {phrase}."
				say(msg)
				setConfig('core', 'username', str(phrase))
				return {'break':single, 'msg':msg}
			
			if "launch" in str(phrase) and "app" in str(phrase):
				current_command = "launch"
				msg = "What application should I launch?"
				say(msg)
				return {'break':False, 'msg':msg}
			
			elif str(phrase).startswith("launch") or str(phrase).startswith("run"):
				rlcm = str(phrase).split(" ")
				rlcm.pop(0)
				phrase = ' '.join(rlcm)
				msg = f"Launching {phrase}"
				say(msg)
				os.system(str(phrase))
				return {'break':single, 'msg':msg}
			else:
				print(f"Check: QUIET_{quiet}")
				msg = f"I heard: {phrase}."
				if not quiet:
					say(msg)
				return {'break':False, 'msg':msg}

		else:
			if current_command == "setname":
				msg = f"Okay, I'll call you {phrase}."
				say(msg)
				setConfig('core', 'username', str(phrase))
			if current_command == "launch":
				msg = f"Launching {phrase}"
				say(msg)
				os.system(str(phrase))
			current_command = ""
			
			return {'break':single, 'msg':msg}
		
	return {'break':False, 'msg':"None"}
		
