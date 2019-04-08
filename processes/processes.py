import multiprocessing
from time import sleep

class AOSProcess:
	def __init__(self, host):
		self.name = type(self).__name__
		self.process = None
		self.host = host
		self.host.threads[self.name] = {'object': self}
		
		print(self.host.threads)
		if not self.host.config.data['processes'].get(self.name):
			pl = self.host.config.data['processes']
			pl[self.name] = False
			self.host.config._set('processes', pl)
			
		if self.host.config._get('processes')[self.name]:
			print(f"Starting {self.name}")
			self.start()
		
	def start(self):
		#print("Checking")
		#print(self.host.threads)

		if self.host.threads[self.name].get('process'):
			return False
		
		self.host.printf(f"Running process thread : {self.name}", tag='info')
		self.process = multiprocessing.Process(target=self.onTrigger, args=())
		self.host.threads[self.name]['process'] = self.process
		self.process.daemon = True
		self.process.start()
		self.host.config.data['processes'][self.name] = True
		self.host.config.save()
		return True
	
	def stop(self):
		self.host.printf(f"Stopping process thread : {self.name}", tag='info')
		try:
			self.process.terminate()
			del self.host.threads[self.name]['process']
			self.host.config.data['processes'][self.name] = False
			self.host.config.save()
			return True
		except KeyError:
			return False
		
	def onTrigger(self):
		while True:
			print("Root task should not be called.")
			sleep(5)
			
class TestProc(AOSProcess):
	def onTrigger(self):
		while True:
			print("This does a thing!")
			sleep(5)
