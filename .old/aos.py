from pocketsphinx import LiveSpeech
import arrow
import os
from Color import *
import asyncio
import json
import sys
from core import *
import art
import argparse

listening = False
freemode = False
repeating = False

current_command = ""

async def begin_cli(single=False, override = ""):
	global listening, current_command
	if override:
		printf(f"Sending: {override}", tag="info")
		resp = await process_commands(override, single)
		return
	
	printf("Loading Athena", tag="info")
	user = touchConfig('core', 'username', os.environ.get('USER'))
	say(f"What do you need, {user}?")
	listening = True

	while True:
		phrase = input("(> ")
		printf(f"Captured: {phrase}", tag="info")
		resp = await process_commands(phrase, single)
		if resp['break']: break

async def begin(single=False):
	global listening, current_command, freemode
	printf("Loading Athena", tag="info")
	user = touchConfig('core', 'username', os.environ.get('USER'))
	if single:
		say(f"I'm listening, {user}.")
		listening = True
	else:
		if repeating:
			say("Repeating your messages.")
		else:
			if listening:
				say(f"Hello {user}. Listener is active.")
			else:
				say(f"Hello {user}. Listener is active. Say my name, Athena, when I'm needed.")
			
	printf("Mic listener active.")

	for phrase in LiveSpeech():
		if repeating:
			if str(phrase) != "": say(str(phrase))
		else:
			if listening:
				printf(f"Captured: {phrase}", tag="info")
				try:
					resp = await process_commands(phrase, single, freemode)
					if resp['break']: break
				except Exception as e:
					say(e)
				#if single: break
				#listening = False
			else:
				printf(f"Checking message for trigger word: {phrase}", tag="info")
				#printf("Checking trigger activator...", tag="info")
				#printf(f"Heard {phrase}")
				if "athena" in str(phrase):
					listening = True
					say("Yes?")

def aos():
	global repeating
	parser = argparse.ArgumentParser(description="Help for AthenaOS Command-Line.")
	parser.add_argument("-s","--single", action="store_true",  help="Listens to one command. Once command is validated, application closes.")
	parser.add_argument("-o","--hold", action="store_true", help="Listener stays running. Say `athena` to trigger, then say a command.")
	parser.add_argument("-f","--free", action="store_true", help="Listener stays running. Any commands heard will run.")
	parser.add_argument("-r","--repeat", action="store_true", help="Listener stays running. TTS speaks every input.")
	parser.add_argument("-sr","--single-repeat", action="store_true", help="TTS speaks first input.")
	parser.add_argument("-c","--command", action="store_true", help="Takes manual text command input.")
	parser.add_argument("-sc","--single-command", action="store_true", help="Like command mode, but closes after a single command is validated.")
	parser.add_argument("-e","--execute",  help="Like command mode, but closes after a single command is validated and skips startup input.")
	args = parser.parse_args()
	print(args)
	art.tprint("ATHENA")
	if args.single:
		asyncio.run(begin(True))
	elif args.hold:
		asyncio.run(begin())
	elif args.free:
		listening = True
		freemode = True
		asyncio.run(begin())
	elif args.command:
		asyncio.run(begin_cli())
	elif args.execute:
		asyncio.run(begin_cli(True, args.execute))
	elif args.single_command:
		asyncio.run(begin_cli(True))
	elif args.single_repeat:
		repeating = True
		asyncio.run(begin(True))
	elif args.repeat:
		repeating = True
		asyncio.run(begin())
	else:
		printf("Closing.", tag="info")
		
if __name__ == "__main__":	
	aos()
