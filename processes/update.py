from time import sleep
	
def notify_update(event):
	while True:
		sleep(10)	
		if event.config._get("has_updates"):
			event.printf("There is an update available.", tag='info')
			event.config._set('has_updates', False)
			
