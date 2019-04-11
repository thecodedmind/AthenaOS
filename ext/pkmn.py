from . import commands
#import pokedex
import tkinter
from tkinter import ttk
import requests
import multiprocessing
import importlib
import humanfriendly

class PokedexCommand(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		
		try:
			#importlib.import_module('pokedex')
			import pokedex
			self.client = pokedex.Pokedex(image_cache=self.host.scriptdir+"cache/")
			self.search = ""
			self.pokemon = {}
			
		except Exception as e:
			print(e)
			print("Pokedex API not available. Download from http://github.com/codedthoughts/pokedex")
			self.disabled = True
			
		self.addListener("pokedex")
		self.addListener("dex")
		self.addListener("pk")
		self.inter = True

	def mpRunPokemon(self):		
		tk = tkinter.Tk()
		
		tk.title(self.pokemon['name'].capitalize())
		self.photo = tkinter.PhotoImage(file=self.client.image_cache+self.pokemon['name'].lower()+'.gif')
		label = tkinter.Label(tk, image=self.photo)
		label.image = self.photo
		label.grid(row=0, column=0, rowspan=20)
		
		r = 2
		tkinter.Label(tk, text=f"Name: {self.pokemon['name'].capitalize()} (ID {self.pokemon['id']})").grid(row=0, column=1)
		tkinter.Label(tk, text=f"Type(s): {self.client.getTypes(self.search.lower())}").grid(row=1, column=1)
		for item in self.client.getTypes(self.search.lower()):
			typeobj = self.client.typeEffectiveness(item)
			if len(typeobj['supereffective']) > 0:
				f = f"{item} is super effective against {humanfriendly.text.concatenate(typeobj['supereffective'])}"
				tkinter.Label(tk, text=f).grid(row=r, column=1)
				
				r += 1
			if len(typeobj['superweak']) > 0:
				f = f"{item} is super weak to {humanfriendly.text.concatenate(typeobj['superweak'])}"
				tkinter.Label(tk, text=f).grid(row=r, column=1)
				
				r += 1
			if len(typeobj['resists']) > 0:
				f = f"{item} takes half damage from {humanfriendly.text.concatenate(typeobj['resists'])}"
				tkinter.Label(tk, text=f).grid(row=r, column=1)
				
				r += 1
			if len(typeobj['halfdmgagainst']) > 0:
				f = f"{item} does half damage to {humanfriendly.text.concatenate(typeobj['halfdmgagainst'])}"
				tkinter.Label(tk, text=f).grid(row=r, column=1)
				
				r += 1
			if len(typeobj['noeffecton']) > 0:
				f = f"{item} has no effect on {humanfriendly.text.concatenate(typeobj['noeffecton'])}"
				tkinter.Label(tk, text=f).grid(row=r, column=1)
				
				r += 1
			if len(typeobj['immuneto']) > 0:
				f = f"{item} completely resists {humanfriendly.text.concatenate(typeobj['immuneto'])}"
				tkinter.Label(tk, text=f).grid(row=r, column=1)
				
				r += 1
		f = tk.mainloop()

	def onTrigger(self, value):
		if self.disabled:
			return self.message("Pokedex API not available. Download from http://github.com/codedthoughts/pokedex")
		
		if value.startswith("type "):
			_t = value.split(" ")[1]
			f = ""
			typeobj = self.client.typeEffectiveness(_t)
			if typeobj.get('error'):
				return self.output(f"Error finding the type.")
			if len(typeobj['supereffective']) > 0:
				f += f"{_t} is super effective against {humanfriendly.text.concatenate(typeobj['supereffective'])}\n"

			if len(typeobj['superweak']) > 0:
				f += f"{_t} is super weak to {humanfriendly.text.concatenate(typeobj['superweak'])}\n"

			if len(typeobj['resists']) > 0:
				f += f"{_t} takes half damage from {humanfriendly.text.concatenate(typeobj['resists'])}\n"

			if len(typeobj['halfdmgagainst']) > 0:
				f += f"{_t} does half damage to {humanfriendly.text.concatenate(typeobj['halfdmgagainst'])}\n"

			if len(typeobj['noeffecton']) > 0:
				f += f"{_t} has no effect on {humanfriendly.text.concatenate(typeobj['noeffecton'])}\n"

			if len(typeobj['immuneto']) > 0:
				f += f"{_t} completely resists {humanfriendly.text.concatenate(typeobj['immuneto'])}\n"

			return self.output(f[:-1])
		
		self.pokemon = self.client.pokemon(value)
		if self.pokemon['name'].startswith("ERROR: "):
			return self.output(f"{self.pokemon['name']}\n{self.pokemon['error']}")
		
		self.client.getSprite(self.pokemon)
		
		self.search = value
		self.process = multiprocessing.Process(target=self.mpRunPokemon, args=())
		self.process.daemon = True
		self.process.start()
		
