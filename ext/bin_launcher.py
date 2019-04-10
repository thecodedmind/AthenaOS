from . import commands
import os

class BinaryRunner(commands.BaseCommand):
	"""
	Simple binary file manager.
	The system is run around the env variable PATHS. All the bins used are read from that.
	Format: bin <subcommand> <args>
	
	
	Sub Commands:
		bin ignore path <path>
			Adds a PATH to ignores so it doesnt show up in the listing.
			
		bin unignore path <path>
			Undo's the above.
			
		bin list paths
			Shows all available directories in PATH.
			Gives each path an ID number that is used for the command below.
			
		bin list bins [arg]
			If arg supplied is a number, lists all bins in the directory matching the ID number from the list.
			If arg is a string, attempts to find a directory matching it, and then lists the bins in that directory.
			If no arg is supplied, lists ALL bins in ALL paths.
		
		bin run <arg>
			Finds if the arg exists in the paths, and runs it.
	"""
	def __init__(self, host):
		super().__init__(host)
		#self.phrases = [self.message("bin"), self.message("brun")]	
		self.addListener("bin")
		self.addListener("brun")
		self.inter = True
	
	def onStart(self):
		self.paths_list = []
		self.paths_raw = os.environ['PATH']
		self.paths_list = self.paths_raw.split(":")
		self.ignored = self.host.config._get('bin_ignored_paths')
		if not self.ignored:
			self.host.config._set('bin_ignored_paths', [])
		for item in self.paths_list:
			if item in self.ignored:
				self.paths_list.remove(item)
				
	def onTrigger(self, value=""):
		if value.startswith("ignore path "):
			value = value[12:]
			for item in self.paths_list:
				if value == item:
					self.ignored.append(value)
					self.host.config._set('bin_ignored_paths', self.ignored)
					
					return self.message(f"Ignored path {value}")
				
			return self.message(f"Failed to ignore path {value}")
		
		elif value.startswith("unignore path "):
			value = value[14:]
			for item in self.ignored:
				if value == item:
					self.ignored.remove(value)
					self.host.config._set('bin_ignored_paths', self.ignored)
					
					return self.message(f"Unignored path {value}")
				
			return self.message(f"Failed to unignore path {value}")
				
		elif value == "list paths":				
			s =  ""
			for item in self.paths_list:
				s += f" [ {self.host.colours.F_Yellow}{self.paths_list.index(item)}{self.host.reset_f} ] {item}\n"
				
			return self.output(s[:-1])
		
		elif value.startswith("list bins "):
			target = value[10:]
			if target.isdigit():
				path = self.paths_list[int(target)]
				s =  f" - Files in {path} -\n"
				
				for file in os.listdir(path):
					filename = os.fsdecode(file)
					s += f" {filename}\n"
					
				return self.output(s[:-1])	
			else:
				path = ""
				for item in self.paths_list:
					print(f"Does {item} start with {target}")
					if item.startswith(target):
						print("Yes!")
						path = item
				
				if path == "":
					return self.message("Incorrect path.")
				
				s =  f" - Files in {path} -\n"
				
				for file in os.listdir(path):
					filename = os.fsdecode(file)
					s += f" {filename}\n"
					
				return self.output(s[:-1])	
			
		elif value.startswith("list bins"):				
			s =  "Not ready yet\n"
				
			return self.output(s[:-1])
				
		elif value.startswith("run "):
			print(value)
			value = value[4:]
			print(value)
			os.system(f'{value}*&')
			
