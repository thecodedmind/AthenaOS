from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from . import commands
import textblob
from textblob import TextBlob, Word
import humanfriendly

class CountTest(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.phrases = [{'message': 'addcount', 'check':100}]
		print("Started counter...")
		
		self.count = 0
		
	def onTrigger(self):
		self.count += 1
		return self.message(f"Count is now {self.count}")
	
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
