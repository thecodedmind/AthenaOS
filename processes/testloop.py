from time import sleep

"""
Background tasks

Functions must exist in a file inside the /tasks directory
They must have one argument that is "event" in order to be considered tasks, otherwise the script ignores them
Event then refers to the commandinfo main class, so the config, Say function, and other things like that can be accessed here
"""

def testloop(event):
	while True:
		print("test")
		sleep(5)
		
def testlooptwo(event):
	while True:
		print("bork")
		sleep(2)	
		
def otherfunction():
	pass
