import json
from . import commands
import memory
from humanfriendly import format_timespan
import os
import psutil

class AudioFindTracks(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("find tracks")
		self.addListener("tracks")
		self.inter = True
	
	def onTrigger(self, value = ""):
		b = self.host.formatting.Bold
		blue = self.host.colours.F_Blue
		r = self.host.reset_f
		f = False
		if value == "":
			s = "\n"
			for item in self.cfg._get('tracks', []):
				ind = self.cfg._get('tracks', []).index(item)
				s += f" {b}[{ind}]{r} {blue}{item[0]}{r} {item[1]}\n"
				
				#s += f"{item[0]} {item[1]}\n"
				f = True
		else:
			s = "\n"
			
			for item in self.cfg._get('tracks', []):
				if value.lower() in item[0] or value.lower() in item[1]:
					ind = self.cfg._get('tracks', []).index(item)
					s += f" {b}[{ind}]{r} {blue}{item[0]}{r} {item[1]}\n"
					f = True
		
		if f:
			return self.output(s)
		else:
			return self.message("Nothing found.")
		
		
class AudioNowPlaying(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("whats playing", 90)
		
	def onTrigger(self, value = ""):
		return self.message(f"{self.cfg._get('currently_playing', 'Nothing.')}")
	
class AudioStorage(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("store a track", 90)		
		self.trackToStore = ""
		
	def onTrigger(self, value = ""):
		return self.hold("Store what?")

	def onHeld(self, value=""):
		if self.trackToStore == "":
			self.trackToStore = value
			return self.hold(f"Storing {value}. What tags should it have? (Seperate each tag with a space)")
		else:
			compiled = [self.trackToStore, value.split()]
			l = self.cfg._get('tracks', [])
			l.append(compiled)
			self.cfg._set('tracks', l)
			self.trackToStore = ""
			return self.output(f"Storing {compiled[0]} with tags {compiled[1]}")

class AudioRemoveStore(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("remove track")
		self.inter = True
		self.trackToStore = ""
		
	def onTrigger(self, value = ""):
		tracks = self.cfg._get('tracks', [])
		if value.isdigit():
			try:
				
				toremove = tracks[int(value)]
				if self.host.promptConfirm(f"Really delete track from list? ({toremove[0]} - {toremove[1]})"):
					del tracks[int(value)]
					self.cfg._set('tracks', tracks)
					return self.message("Track deleted.")
			except:
				return self.message("Track not found.")
		else:
			for item in tracks:
				if value.lower() in item[0].lower():
					toremove = tracks[tracks.index(item)]
					if self.host.promptConfirm(f"Really delete track from list? ({toremove[0]} - {toremove[1]})"):
						del tracks[tracks.index(item)]
						self.cfg._set('tracks', tracks)
						return self.message("Track deleted.")
		
class AudioPlayer(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("play")
		self.inter = True
		
	
	#def onRun(self):
		#self.cfg._set('currently_playing', "Nothing.")
		
	def onTrigger(self, value = ""):
		track = ""
		tracks = self.cfg._get('tracks', [])
		
		if value.isdigit():
			try:
				track = tracks[int(value)][0]
				self.host.printf(f"Loading track {track}")
			except:
				return self.message(f"Tried to find track at index {value} but failed.")
		else:
			for item in tracks:
				if value.lower() in item[0].lower():
					track = tracks[tracks.index(item)][0]		
					self.host.printf(f"Loading track {track}")
					
		if track == "":
			track = value
		
		for p in psutil.process_iter():
			if p.name() == "ffplay":
				self.host.printf("Stopping current track.", tag='info')
				p.kill()
		
		if not self.cfg._get('audio_viz', False):
			g = " -nodisp"
		else:
			g = ""
		os.system(f'ffplay "{track}"{g} -autoexit -loglevel quiet&')
		self.cfg._set('currently_playing', track)
		return self.message(f"Playback of {track} started.")
	
class AudioStop(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("stop", 100)
		
	def onTrigger(self, value = ""):
		for p in psutil.process_iter():
			if p.name() == "ffplay":
				self.cfg._set('currently_playing', "Nothing.")
				p.kill()
