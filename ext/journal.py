import json
from . import commands
import arrow
import memory
from humanfriendly import format_timespan

class JournalManager(commands.BaseCommand):
	"""
	Journal Manager
	
	Sub Commands:
		journal add <message> -> adds message to journal, timestamping it
		
		journal delete <id> -> deletes journal entry by ID
		
		journal annotate <id> <message> -> adds a note to the specified entry
		
		journal edit <id> -> opens interactive editor
		
		journal view <id> -> prints journal entry for that ID
		
		journal find <query> -> prints entries matching certain methods. For now, the following tags are supported
			-Ready-
			+today
			+thisweek
			+yesterday
			
			-Planned-
			+lastweek
			+thismonth
			+lastmonth
			+thisyear
			+lastyear
	"""
	def __init__(self, host):
		super().__init__(host)
		self.addListener("journal")
		self.inter = True
		self.journal = memory.Memory(path=self.host.scriptdir+'journal.json')
	
	def addJournalEntry(self, msg):
		entries = self.entries()
		
		new_data = {
			'message': msg,
			'timestamp': arrow.now().format('YYYY-MM-DD HH:mm')
		}
		entries.append(new_data)
		_new_id = entries.index(new_data)
		self.journal._set('entries', entries)
		return _new_id
	
	def entries(self, gets = None):
		if gets == None:
			return self.journal._get('entries', [])
		else:
			try:
				return self.journal._get('entries', [])[int(gets)]
			except:
				return None
	
	def getInd(self, raw):
		return self.entries().index(raw)
	
	def onTrigger(self, value=""): 
		b = self.host.formatting.Bold
		blue = self.host.colours.F_Blue
		r = self.host.reset_f
		
		if value == "":
			s = f"There are {len(self.entries())} entries.\n"
			
			if len(self.entries()) > 0:
				last = arrow.get('1999', 'YYYY')
				for item in self.entries():
					then = arrow.get(item['timestamp'], 'YYYY-MM-DD HH:mm')
					if then > last:
						#print(item)
						last = then
				
				sr = arrow.now() - last
				s += f"Last entry was on {last.format('YYYY-MM-DD HH:mm')}."
			
			return self.message(s)
		#takes string and adds to list
		if value.startswith('add '): 
			value = value[4:]
			res = self.addJournalEntry(value)
			
			j = self.entries()[res]
			ts = j['timestamp']
			msg = j['message']
			return self.output(f"{ts}\n{msg}\n--SAVED--")
		
		if value == "list" or value == "ls":
			out = "\n"
			for item in self.entries():
				ind = self.getInd(item)
				out += f" {b}[{ind}]{r} {blue}{self.entries(ind)['timestamp']}{r} -> {self.entries(ind)['message']}\n"
			
			return self.output(out)
		
		#deletes by ID, needs confirm	
		if value.startswith('delete '): 
			value = value[7:]
			entries = self.entries()
			
			if not value.isdigit():
				return self.message("Value has to be an index number.")
			
			i = int(value)
			try:
				self.host.printf(f"({entries[i]['timestamp']}) -> {entries[i]['message']}", tag='info', ts=False)
				if self.host.promptConfirm(f"Really delete entry?"):
					del entries[i]
					self.journal._set('entries', entries)
					return self.message("Entry deleted.")
				else:
					return self.message("Cancelling.")
			except:
				return self.message("Entry not found on that index.")
			
		#edits by ID, then holds asking for what to edit, reply should be <key> <new value> #j becomes whatevers currently there, useful for appending
		#Note to self, keep an edit history in each entry dict somehow
		if value.startswith('edit '): 
			value = value[5:]
			
		#annotates <id> with <message>, so when the journal entry is viewed, it'll show the annotation
		#add annotating to the edit history of the entry
		if value.startswith('annotate '):
			value = value[9:]
			
		#shows entry at ID 
		if value.startswith('view '):
			value = value[5:]
			
			if self.entries(value):
				# TODO add support for annotations and edit history
				return self.output(f" {b}[{value}]{r} {blue}{self.entries(value)['timestamp']}{r} -> {self.entries(value)['message']}")
			else:
				return self.message("Entry does not exist.")
			
		#Searches by certain criteria
		if value.startswith('find '):
			value = value[5:]
			out = "\n"
			valid = []
			today = arrow.now()
			for item in self.entries():
				# add a +all which adds all
				# at the end of the +'s, add matching -'s that REMOVES matching items from valid
				#print(item)
				_id = self.entries().index(item)
				target = arrow.get(item['timestamp'], 'YYYY-MM-DD HH:mm')
				if "+today" in value:
					if today.day == target.day and today.month == target.month and today.year == target.year:
						valid.append(_id)
							
				if "+yesterday" in value:
					if (today.day-1) == target.day and today.month == target.month and today.year == target.year:
						valid.append(_id)

				if "+thisweek" in value:
					if today.isocalendar()[1] == target.isocalendar()[1]:
						valid.append(_id)
			
				if "+lastweek" in value:
					if (today.isocalendar()[1]-1) == target.isocalendar()[1]:
						valid.append(_id)
						
				if "+thismonth" in value:
					if today.month == target.month and today.year == target.year:
						valid.append(_id)
						
				if "+lastmonth" in value:
					if (today.month-1) == target.month and today.year == target.year:
						valid.append(_id)
				if "+thisyear" in value:
					if today.year == target.year:
						valid.append(_id)
				if "+lastyear" in value:
					if (today.year-1) == target.year:
						valid.append(_id)
						
			#print("At validated.")
			if len(valid) > 0:
				valid = list(set(valid)) # TODO add support for showing the annotations
				#print("Sorted")
				for item in valid:
					#print(item)
					
					out += f" {b}[{item}]{r} {blue}{self.entries(item)['timestamp']}{r} -> {self.entries(item)['message']}\n"
				
	
				return self.output(out)
			else:
				return self.message("Nothing was found.")
