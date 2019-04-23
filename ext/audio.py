import json
from . import commands
import memory
from humanfriendly import format_timespan
import os
import psutil
import shlex

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
	
class AudioStorageCurrently(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("store this track", 95)		
		self.trackToStore = ""
		
	def onTrigger(self, value = ""):
		if self.cfg._get('currently_playing', '') == "":
			return self.message(f"Nothing is playing right now.")
		else:
			self.trackToStore = self.cfg._get('currently_playing', '')
			return self.hold(f"Storing {self.cfg._get('currently_playing', '')}. What tags should it have?")
			
	def onHeld(self, value = ""):
		compiled = [self.trackToStore, shlex.split(value)]
		l = self.cfg._get('tracks', [])
		l.append(compiled)
		self.cfg._set('tracks', l)
		self.trackToStore = ""
		return self.output(f"Storing {compiled[0]} with tags {compiled[1]}")

class AudioStorage(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("store a track", 95)		
		self.trackToStore = ""
		
	def onTrigger(self, value = ""):
		return self.hold("Store what?")

	def onHeld(self, value=""):
		if value == "":
			return self.message("Cancelling.")
		
		if self.trackToStore == "":
			self.trackToStore = value
			return self.hold(f"Storing {value}. What tags should it have? (Seperate each tag with a space)")
		else:
			compiled = [self.trackToStore, shlex.split(value)]
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
		try:
			import youtube_dl
			youtube_support = True
		except:
			print("Youtube-dl module error. Disabling youtube support.")
			youtube_support = False
	
	#def onRun(self):
		#self.cfg._set('currently_playing', "Nothing.")
		
	def onTrigger(self, value = ""):
		b = self.host.formatting.Bold
		blue = self.host.colours.F_Blue
		r = self.host.reset_f
		track = ""
		tracks = self.cfg._get('tracks', [])
		
		valid_tracks = []
		if value.isdigit():
			try:
				track = tracks[int(value)][0]
				self.host.printf(f"Loading track {track}")
			except:
				return self.message(f"Tried to find track at index {value} but failed.")
		else:
			for item in tracks:
				if value.lower() in item[0].lower() or value.lower() in item[1]:
					valid_tracks.append(item)
				
				
			if len(valid_tracks) == 1:
				track = valid_tracks[0][0]
				self.host.printf(f"Loading track {track}")
		
			elif len(valid_tracks) > 1:
				prompt = "\n"
				for i in valid_tracks:
					prompt += f" {b}{valid_tracks.index(i)}{r}: {blue}{i[0]}{r} {i[1]}\n"
				self.host.printf(f"Multiple tracks were found matching that search, enter a number to continue:\n{prompt}")
				track_name = input("Enter: ")
				if track_name.isdigit():
					track = valid_tracks[int(track_name)][0]	
					self.host.printf(f"Loading track {track}")
				else:
					return self.message("Not a number.")
				
			
		if track == "":
			track = value
		
		if not self.cfg._get('audio_viz', False):
			g = " -nodisp"
		else:
			g = ""
			
		
		if track.startswith("http"):
			self.stopAudio()
			if "youtube.com" in track:
				print("Detected youtube URL.")
				self.cfg._set('currently_playing', track)
				os.system(f'youtube-dl -q -o - {track} | ffplay -{g} -autoexit -loglevel quiet&')
				return self.message(f"Playback of youtube video starting. This could take a moment depending on your system.")
			
			os.system(f'ffplay "{track}"{g} -autoexit -loglevel quiet&')
			self.cfg._set('currently_playing', track)
			return self.message(f"Playback of {track} started.")
		else:
			return self.message(f"PLACEHOLDER: Will search for track {track}.")
	
	def stopAudio(self):
		for p in psutil.process_iter():
			if p.name() == "ffplay":
				self.host.printf("Stopping current track.", tag='info')
				p.kill()
				
class AudioStop(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("stop", 100)
		
	def onTrigger(self, value = ""):
		for p in psutil.process_iter():
			if p.name() == "ffplay":
				self.cfg._set('currently_playing', "Nothing.")
				p.kill()
