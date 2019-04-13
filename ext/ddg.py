from . import commands 
import random

class DuckDuckGo(commands.BaseCommand):
	"""
	Searches DuckDuckGo and prints the results.
	
	format:
		search for <anything>
		
		If needed, adding /number to the query shows only the one result, for example
		search for python3 /5
		shows the 5th result, otherwise top 10 results will be shown.
	"""
	def __init__(self, host):
		super().__init__(host)
		
		try:
			import duckduckgo
			self.client = duckduckgo.DDG('AOSR')
			
		except Exception as e:
			print(e)
			print("DDG API not available. Download from http://github.com/codedthoughts/duckduckgo")
			self.disabled = True
			
		self.addListener("ddg")
		self.addListener("search for ")
		self.inter = True
	
	def doSearch(self, value):
		num = -1
		for i in range(0, 10):
			if f'/{i}' in value:
				value = value.replace(f'/{i}', '')
				num = i
		
		if num == -1:
			data = self.client.search(value)
			s = ""
			for i in range(0, 10):
				try:
					s += f"{data['snippets'][i]}\nhttp://{data['urls'][i]}\n\n"
					f = True
				except IndexError:
					pass
				
			if s != "":
				return s[:-2]
			else:
				return "No results found."

		data = self.client.search(value)
		
		try:
			return f"{self.host.formatting.Bold}[Search for {value} (RESULT: {num})]{self.host.reset_f}\n{data['snippets'][num]}\nhttp://{data['urls'][num]}"
		except IndexError:
			return "No result on that index."
			
	def onHeld(self, value):
		return self.output(self.doSearch(value))
	
	def onTrigger(self, value = ""):
		if self.disabled:
			return self.message("DDG API not available. Download from http://github.com/codedthoughts/duckduckgo")
		
		if value == "":
			return self.hold("Search for what?")
		return self.output(self.doSearch(value))
