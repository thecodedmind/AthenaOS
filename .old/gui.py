import tkinter
from tkinter import ttk
import os
import asyncio
from textblob import TextBlob
from pocketsphinx import LiveSpeech
from core import *
import art
import subprocess
from kui import *

class AthenaGUI:
	def init_root(self):
		self.w = tkinter.Tk()
		self.w.title("Athena")
		self.welc = tkinter.Label()
		self.en = tkinter.Entry(self.w, width=30)
		self.enter = ttk.Button(self.w, text="Submit", command=self.submit_data, cursor="hand1")
		self.w.bind('<Return>', self.submit_data)
		self.mic = ttk.Button(self.w, text="Listen", command=self.catch_mic, cursor="hand1")
		self.w.bind('<F2>', self.catch_mic)
		#self.w.bind('<F3>', self.cancel_mic)
		self.en.grid(column=0, row=0, sticky="we")
		self.enter.grid(column=1, row=0, sticky="we")
		self.mic.grid(column=2, row=0, sticky="we")
		self.op = OutputWindow(master_window=self.w)
		self.op.frame.grid(column=0, row=1, columnspan=3, sticky="nswe")
					
		for i in range(0, 3):
			self.w.columnconfigure(i, weight=1)
		
		self.w.rowconfigure(1, weight=1)
		self.w.mainloop()
	
		
	def cancel_mic(self, event=None):
		asyncio.run(self.spch.cancel())
		
	def catch_mic(self, event=None):
		asyncio.run(self.spch.run())
	
	async def post_command(self, command):	
		
		resp = await process_commands(command)
		printf(resp)
		
		self.op.insert(f"Athena: {resp['msg']}", font="green", index='1.0')
		self.op.insert(f"You: {command}", font="gray", index='1.0')
		if resp['break']: self.w.destroy()
			
	def submit_data(self, event=None):

		asyncio.run(self.post_command(self.en.get()))
		try: self.en.delete(0, 'end') 
		except: pass
	
root = AthenaGUI()		
root.init_root()
