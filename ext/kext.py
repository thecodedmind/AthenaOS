from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from . import commands
import textblob
from textblob import TextBlob, Word
import humanfriendly
import random

class CountTest(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'addcount', 'check':100}]
		print("Started counter...")
		
		self.count = 0
		
	def onTrigger(self):
		self.count += 1
		return self.message(f"Count is now {self.count}")

class EightBall(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [self.message("8ball")]
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

class Dice(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [self.message("roll"), self.message("dice")]
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

			return self.message(f"You rolled: {dies_string}. (Total: {dies_total})")
		except IndexError:
			return self.message("Error in notation; example is `2d6`.")
		except ValueError:
			return self.message("One of the values is not a real number.")
		except Exception as e:
			return self.message(f"Some problem; {e}")
			
class Flip(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'flip a coin', 'check': 90}]
	
	def onTrigger(self):
		if random.random() > 0.5:
			return self.message(f"It landed Heads!")
		else:
			return self.message(f"It landed Tails!")
	
class Choice(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [self.message("choice"), self.message("choose")]
		self.inter = True
	
	def onTrigger(self, value):
		choices = value.split()
		return self.message(f"Between {humanfriendly.text.concatenate(choices)}, I choose {random.choice(choices)}.")
	
class Repeat(commands.BaseCommand):
	"""
	Bot repeats whatever is said.
	[BASE EXT]
	~Kaiser
	"""
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'repeat'}, {'message': 'say'}]
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
		self.phrases = [{'message': 'translate'}]
		self.inter = True
	
	def translateWord(self, text, lang):
		print(text)
		print(lang)
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
		self.phrases = [{'message': 'define'}]
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
		self.phrases = [{'message': 'call me'}, {'message': 'change my name to'}]
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
		self.phrases = [{'message': 'who am i?', 'check': 90}, {'message': 'what is my name?', 'check': 90}]
		
	def onTrigger(self):
		return {'message': f"You are {self.host.config._get('username')}"}
