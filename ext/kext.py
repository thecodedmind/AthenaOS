from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from . import commands
import textblob
from textblob import TextBlob, Word
import humanfriendly
import random
import shlex
import os

def isfloat(value):
	try:
		float(value)
		return True
	except ValueError:
		return False

class Calculate(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("calculate")
		self.inter = True
		
	def onTrigger(self, value=""):
		try:
			value = eval(cstr, {})
			return self.message(str(value))
		except Exception as e:
			return self.message("Syntax error.")
		
class CountersAdd(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("add")
		self.inter = True
		
	def onTrigger(self, value = ""):
		counters = self.host.config._get('counters', {})
		args = shlex.split(value)
		if len(args) < 2:
			return self.message("Missing argument, example format is 'add x to y'.")
		
		if len(args) == 2:
			vmod = args[0]
			key = args[1]

		if len(args) == 3:
			if args[1] != "to":
				return self.message("Didn't understand the input.")
			
			vmod = args[0]
			key = args[2]
			if not vmod.isdigit() and not isfloat(vmod):
				return self.message("Value is not a valid number.")
			
			try:
				counters[key] += float(vmod)
			except:
				counters[key] = float(vmod)
				
			self.host.logAction('counters_'+key, f"ADDED - Now {counters[key]}")
			self.host.config._set('counters', counters)
			return self.message(f"{key} is now {counters[key]}")

class CountersSub(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("take")
		self.inter = True
		
	def onTrigger(self, value = ""):
		counters = self.host.config._get('counters', {})
		args = shlex.split(value)
		if len(args) < 2:
			return self.message("Missing argument, example format is 'take x from y'.")
		
		if len(args) == 2:
			vmod = args[0]
			key = args[1]

		if len(args) == 3:
			if args[1] != "from":
				return self.message("Didn't understand the input.")
			vmod = args[0]
			key = args[2]
			if not vmod.isdigit() and not isfloat(vmod):
				return self.message("Value is not a valid number.")
			
			try:
				counters[key] -= float(vmod)
			except:
				counters[key] = 0.0
				counters[key] -= float(vmod)
			self.host.logAction('counters_'+key, f"SUBTRACTED - Now {counters[key]}")
			self.host.config._set('counters', counters)
			return self.message(f"{key} is now {counters[key]}")
	
class CountersController(commands.BaseCommand):
	"""
	Counter manager
	
	Commands:
		counters [counter name] - If no sub-command given, shows all counters. Otherwises shows specific counter.
		counters add/sub/div/mul/set <counter name> <value> - Modifies value of counter
		counters delete <counter name> - Deletes a counter
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("counters")
		self.addListener("counter")
		
		self.inter = True

	def onTrigger(self, value = ""):
		counters = self.host.config._get('counters', {})
		if value == "":
			cl = ""
			for item in counters:
				cl += f"{item} is at {counters[item]}\n"
			return self.message(f"There are {len(counters)} counters.\n{cl[:-1]}")

		#Make `add`, `take/sub`, `set`, `mult`, `div`
		#Make global commands `multiply x by y` and `divide x by y`
		
		if value.startswith("add "):
			value = value[4:]
			args = value.split()
			if not args[1].isdigit() and not isfloat(args[1]):
				return self.message("Invalid number."
						)
			try:
				counters[args[0]] += float(args[1])
			except:
				counters[args[0]] = float(args[1])
				
			self.host.config._set('counters', counters)
			self.host.logAction('counters_'+args[0], f"ADDED - Now {counters[args[0]]}")
			return self.message(f"{args[0]} is now {counters[args[0]]}")
		
		if value.startswith("sub "):
			value = value[4:]
			args = value.split()
			if not args[1].isdigit() and not isfloat(args[1]):
				return self.message("Invalid number."
						)
			try:
				counters[args[0]] -= float(args[1])
			except:
				counters[args[0]] = 0
				counters[args[0]] -= float(args[1])
			self.host.config._set('counters', counters)
			self.host.logAction('counters_'+args[0], f"SUBTRACTED - Now {counters[args[0]]}")
			return self.message(f"{args[0]} is now {counters[args[0]]}")
		
		if value.startswith("div "):
			value = value[4:]
			args = value.split()
			if not args[1].isdigit() and not isfloat(args[1]):
				return self.message("Invalid number."
						)
			try:
				counters[args[0]] /= float(args[1])
			except:
				counters[args[0]] = 0
				counters[args[0]] /= float(args[1])
			self.host.config._set('counters', counters)
			self.host.logAction('counters_'+args[0], f"DIVIDED - Now {counters[args[0]]}")
			return self.message(f"{args[0]} is now {counters[args[0]]}")
		
		if value.startswith("mul "):
			value = value[4:]
			args = value.split()
			if not args[1].isdigit() and not isfloat(args[1]):
				return self.message("Invalid number.")
			
			try:
				counters[args[0]] *= float(args[1])
			except:
				counters[args[0]] = 0
				counters[args[0]] *= float(args[1])
			self.host.config._set('counters', counters)
			self.host.logAction('counters_'+args[0], f"MULTIPLIED - Now {counters[args[0]]}")
			return self.message(f"{args[0]} is now {counters[args[0]]}")
		
		if value.startswith("set "):
			value = value[4:]
			args = value.split()
			if not args[1].isdigit() and not isfloat(args[1]):
				return self.message("Invalid number.")

			counters[args[0]] = float(args[1])
			self.host.config._set('counters', counters)
			self.host.logAction('counters_'+args[0], f"SET - Now {counters[args[0]]}")
			return self.message(f"{args[0]} is now {counters[args[0]]}")
		
		if value.startswith("delete "):
			value = value[7:]
			try:
				del counters[value]
				self.host.config._set('counters', counters)
				self.host.logAction('counters_'+args[0], f"ERASED")
				return self.message(f"Value {value} deleted.")
			except:
				return self.message(f"{value} does not exist.")
			
		try:
			return self.message(f"{value} is at {counters[value]}")
		except:
			return self.message(f"{value} does not exist.")
		
class Speak(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("speak", 95)
		self.addListener("speak up", 90)
	
	def onTrigger(self):
		if not self.host.config._get('tts'):
			self.host.config._set("tts", True)
			return self.message("Speech enabled.")
		else:
			return self.message("Speech is already on.")
		
class Quieten(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("quiet", 95)
		self.addListener("be quiet", 90)
		self.addListener("no talking", 95)
		self.addListener("shush", 95)
		self.addListener("shhh", 90)
	
	def onTrigger(self):
		if not self.host.config._get('tts'):
			return self.message("Already quiet.")
		else:
			self.host.config._set("tts", False)
			return self.message("Okay, speech off.")
		
class DiskSearchLocate(commands.BaseCommand):
	"""
	Disk searching tools.
	
	Commands:
		disk locate <file name>
			Searches the disk for files matching this name
			
		disk inspect <path> <word(s)> [optional file extension]
			Searches the <path> for files that contain <words> in the body. If a file extension is supplied, restricts files to that type, e.g. txt files, ini files.
			If the file path or words needs spaces in them, surround the section with quote marks, e.g.
			disk inspect "home/user/My Documents/" "stuff here" txt
			
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("disk")
		self.inter = True
	
	def run_dchk(self, path, check, fileext = ""):
		if not path.endswith("/"):
			path = path+"/"
		full = "Checking "+path+" *"+fileext+" for "+check+"...\n"
		found = []
		
		try:
			for file in os.listdir(path):
				try:
					filename = os.fsdecode(file)
					if not os.path.isfile(path+filename):
						full += f"Skipping directory {filename}\n"
					else:
						if filename.endswith(fileext):
							full += f"Opening {filename}\n"
							with open(path+filename, "rb") as fl:
								cont = str(fl.read(), "latin-1")
								if check.lower() in cont.lower():
									found.append(filename)
								
				except Exception as e:
					full += f"{e}\n"
				
		except Exception as e:
			return e
		
		full += f"{len(found)} found.\n{self.host.humanizeList(found)}"
		return full
	
	def onTrigger(self, value):
		if value.startswith("locate "):
			value = value[7:]
			print("Searching for "+value)
			return self.output(self.host.terminal(f"locate {value}"))
		
		elif value.startswith("inspect "):
			value = value[8:]
			v = shlex.split(value)
			if len(v) < 3:
				v.append("")
				
			if len(v) < 3:
				return self.message("Missing an argument for that.")
			
			s = self.run_dchk(v[0], v[1], v[2])
			return self.output(s)
		
class EightBall(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("8ball")
		self.inter = True
	
	def onTrigger(self, value):
		responses = ["as I see it, yes",
		"ask again later",
		"better not tell you now",
		"cannot predict now",
		"concentrate and ask again",
		"don’t count on it",
		"it is certain",
		"it is decidedly so",
		"most likely",
		"my reply is no",
		"my sources say no",
		"outlook good",
		"outlook not so good",
		"reply hazy try again",
		"signs point to yes",
		"very doubtful",
		"without a doubt",
		"yes",
		"yes, definitely",
		"you may rely on it"]
		res = random.choice(responses)
		return self.message(res.capitalize()+".")

class RollRNG(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("roll")
		self.addListener("rng")
		self.inter = True
		
	def onTrigger(self, value):
		if value == "":
			value = "10"
		if not value.isdigit():
			return self.message("Value must be a number.")
		random.randint(0, int(value))
		return self.message(f"You rolled {random.randint(0, int(value))} out of {value}.")
	
class Dice(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("dice")
		self.inter = True
		
	def onTrigger(self, value):
		notation = value
		try:
			dm = 0
			if "+" in notation:
				dm = int(notation.split("+")[1]) #modifier; 2d12+2 adds 2 to total
				notation = notation.split("+")[0]
			dn = int(notation.split("d")[0]) #number of die; eg 2d12 is 2
			ds = int(notation.split("d")[1]) #sides of the die; eg 2d12 is 12
			if dn <= 0 or ds <= 1:
				return self.message("Dice count should be above 1 and sides should be above 0.")
			
			dies = []
			while dn > 0:
				dies.append(random.randint(1, ds))
				dn -= 1

			dies_sl = []
			dies_total = 0
			for item in dies:
				dies_total += int(item)
				dies_sl.append(str(item))
			
			if dm > 0:
				dies_total += dm
				dies_total = f"{dies_total} (+{dm})"
				
			dies_string = humanfriendly.text.concatenate(dies_sl)

			return self.message(f"You rolled {dies_string}. (Total: {dies_total})")
		except IndexError:
			return self.message("Error in notation; example is `2d6`.")
		except ValueError:
			return self.message("One of the values is not a real number.")
		except Exception as e:
			return self.message(f"Some problem; {e}")
			
class Flip(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("flip a coin", 90)
		
	def onTrigger(self):
		if random.random() > 0.5:
			return self.message(f"It landed Heads!")
		else:
			return self.message(f"It landed Tails!")
	
class Choice(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("choose between")
		self.addListener("choose from")
		self.inter = True
	
	def onTrigger(self, value):
		value = value.replace(",", "")
		value = value.lower()
		choices = value.split()
		for item in choices:
			if item == "and" or item == "or":
				choices.remove(item)
		
		return self.message(f"Between {humanfriendly.text.concatenate(choices)}, I choose {random.choice(choices)}.")
	
class Repeat(commands.BaseCommand):
	"""
	Bot repeats whatever is said.
	[BASE EXT]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("repeat")
		self.addListener("say")
		self.inter = True
	
	def onTrigger(self, value = ""):
		if value == "":
			return self.hold("Say what?")
		
		return {'message': value}
	
	def onHeld(self, value):
		return {'message': value}

class Translate(commands.BaseCommand):
	"""
	Translates words
	[BASE EXT]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("translate")
		self.inter = True
	
	def translateWord(self, text, lang):
		try:
			blob = TextBlob(text)
			try:
				return blob.translate(to=lang)
			except textblob.exceptions.NotTranslated:
				return "The text was not translated. Are you trying to translate to and from the same language, or the word couldn't be translated?"
			except textblob.exceptions.TranslatorError:
				return "There was an error on the translator side. Maybe try again later?"
		except RuntimeError:
			blob = TextBlob(text)
			try:
				return blob.translate(to=lang)
			except textblob.exceptions.NotTranslated:
				return "The text was not translated. Are you trying to translate to and from the same language, or the word couldn't be translated?"
			except textblob.exceptions.TranslatorError:
				return "There was an error on the translator side. Maybe try again later?"
	
	def onTrigger(self, value = ""):
		if value == "":
			return {'message': 'A phrase is needed.'}
		
		if value.split(" ")[-2] == "to":
			tolang = value[-2:]
			value = value[:-6]
			return {'message': self.translateWord(value, tolang)}
		else:
			return {'message': "Bad language choice."}
		
class Define(commands.BaseCommand):
	"""
	Shows word definitions
	[BASE EXT]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("define")
		self.inter = True
	
	def defineWord(self, word):
		with humanfriendly.AutomaticSpinner("Loading, this can take awhile for the first time, but repeating the command again will be considerably faster..."):
			try:
				blob = Word(word)
				defs = blob.definitions
				s = ""
				if len(defs) > 0:
					for item in defs[0:4]:
						s += item.capitalize()+".\n"
					return s
				else:
					return "No result found."
			except RuntimeError:	
				blob = Word(word)
				defs = blob.definitions
				s = ""
				if len(defs) > 0:
					for item in defs[0:4]:
						s += item.capitalize()+".\n"
					return s
				else:
					return "No result found."
	
	def onTrigger(self, value = ""):
		if value == "":
			return self.hold("Define what?")
		
		
		return {'message': self.defineWord(value.split(" ")[0])}
	
	def onHeld(self, value):
		return {'message': self.defineWord(value.split(" ")[0])}
	
class CallMeName(commands.BaseCommand):
	"""
	Changes your name
	[BASE EXT]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("call me")
		self.addListener("change my name to")
		self.inter = True
		
	def onTrigger(self, value = ""):
		self.host.config._set('username', value)
		return {'message': f"You are now {self.host.config._get('username')}."}
	
class WhoAmI(commands.BaseCommand):
	"""
	Shows your current set display name.
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("who am i?", 90)
		self.addListener("what is my name?", 90)
		
	def onTrigger(self):
		return {'message': f"You are {self.host.config._get('username')}."}
