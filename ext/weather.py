import json
from darksky import forecast
from unit_parser import unit_parser
import datetime
from . import commands
import requests
from pytz import timezone

class WeatherCheck(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("how is the weather", 95)
		self.addListener("how's the weather", 95)
		self.addListener("how's my weather", 95)
		self.addListener("how is it outside", 95)
		
	def onTrigger(self, value=""):
		
		if self.host.config._get('location', "") != "":
			location = self.host.config._get('location', "")
		else:
			return self.message("No location found. 'set location to x'")
		
		if self.host.config._get('weather_token', "") != "":
			pass
		else:
			return self.message("An API token for Darksky is required for the weather module. Check their website, get a token, then 'set weather_token to your_token'")

		location_arg = location	

		if " " in location:
			location = location.replace(" ", "+")
		
		res = requests.get(f"http://photon.komoot.de/api/?q={location}").text
		gl = json.loads(res)
		
		if len(gl['features']) == 0:
			return self.message("Problem looking up that location")
			
		lat = gl['features'][0]['geometry']['coordinates'][1]
		lng = gl['features'][0]['geometry']['coordinates'][0]
		
		try:
			city = 	gl['features'][0]['properties']['city']	
		except:
			city = 	gl['features'][0]['properties']['country']	

		weather = forecast(self.host.config._get('weather_token'), lat, lng)

		if weather is None:
			return self.message("No data found.")
			
		alerts = 0
		try:
			alerts = len(weather.alerts)
		except:
			pass
		
		astr = ""
		if alerts > 1:
			astr = f"There are {alerts} alerts for this location. Say 'show me my weather alerts' for more information'.\n"
		elif alerts == 1:
			astr = f"There is an alert for this location. Say 'show me my weather alerts' for more information'.\n"	
			
		precip = ""
		
		try:
			if weather.precipProbability != 0:
				precip += f"There is a {str(weather.precipProbability*100).split('.')[0]}% chance of"
				try:
					precip += f" {weather.precipType}, "
				except:
					precip += " some weathery thing, "
		except:
			pass
		
		try:
			if weather.precipIntensity != 0:
				up = unit_parser()
				wpinmm = up.convert(f"{weather.precipIntensity}inches", "mm")
				precip += f" {weather.precipIntensity} in/hour ({wpinmm}mm/hour)..\n"
		except:
			pass
		
		converted_temp = str((weather.temperature - 32) * 5/9).split(".")[0]

		f_temp = str(weather.temperature).split('.')[0]
		
		local_time = datetime.datetime.now(timezone(weather.timezone))
		if local_time.minute < 10:
			f_min = f"0{local_time.minute}"
		else:
			f_min = local_time.minute
			
		return self.message(f"Weather report for {city}, {weather.timezone}.\nThe local time is {local_time.hour}:{f_min} on {local_time.day}/{local_time.month}/{local_time.year}.\nIt is currently {f_temp}°F/{converted_temp}°C. ({str(weather.humidity).split('.')[1]}% humidity)\nThe current weather is {weather.summary}{astr}{precip}.")
	
class WeatherOtherCheck(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("how is the weather in")
		self.addListener("how's the weather in")
		self.addListener("hows the weather in")
		self.inter = True
		
	def onTrigger(self, value=""):
		if self.host.config._get('weather_token', "") != "":
			pass
		else:
			return self.message("An API token for Darksky is required for the weather module. Check their website, get a token, then 'set weather_token to your_token'")

		location = value
		location_arg = location	

		if " " in location:
			location = location.replace(" ", "+")
		
		res = requests.get(f"http://photon.komoot.de/api/?q={location}").text
		gl = json.loads(res)
		
		if len(gl['features']) == 0:
			return self.message("Problem looking up that location")
			
		lat = gl['features'][0]['geometry']['coordinates'][1]
		lng = gl['features'][0]['geometry']['coordinates'][0]
		
		try:
			city = 	gl['features'][0]['properties']['city']	
		except:
			city = 	gl['features'][0]['properties']['country']	

		weather = forecast(self.host.config._get('weather_token'), lat, lng)

		if weather is None:
			return self.message("No data found.")
			
		alerts = 0
		try:
			alerts = len(weather.alerts)
		except:
			pass
		
		astr = ""
		if alerts > 1:
			astr = f"There are {alerts} alerts for this location. Say 'show me my weather alerts' for more information'.\n"
		elif alerts == 1:
			astr = f"There is an alert for this location. Say 'show me my weather alerts' for more information'.\n"	
			
		precip = ""
		
		try:
			if weather.precipProbability != 0:
				precip += f"There is a {str(weather.precipProbability*100).split('.')[0]}% chance of"
				try:
					precip += f" {weather.precipType}, "
				except:
					precip += " some weathery thing, "
		except:
			pass
		
		try:
			if weather.precipIntensity != 0:
				up = unit_parser()
				wpinmm = up.convert(f"{weather.precipIntensity}inches", "mm")
				precip += f" {weather.precipIntensity} in/hour ({wpinmm}mm/hour)..\n"
		except:
			pass
		
		converted_temp = str((weather.temperature - 32) * 5/9).split(".")[0]

		f_temp = str(weather.temperature).split('.')[0]
		
		local_time = datetime.datetime.now(timezone(weather.timezone))
		if local_time.minute < 10:
			f_min = f"0{local_time.minute}"
		else:
			f_min = local_time.minute
			
		return self.message(f"Weather report for {city}, {weather.timezone}.\nThe local time is {local_time.hour}:{f_min} on {local_time.day}/{local_time.month}/{local_time.year}.\nIt is currently {f_temp}°F/{converted_temp}°C. ({str(weather.humidity).split('.')[1]}% humidity)\nThe current weather is {weather.summary}{astr}{precip}.")
	
class WeatherAlertCheck(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("show me my weather alerts", 95)
		self.addListener("show the weather alerts", 95)
		self.addListener("show my weather alerts", 95)
		
	def onTrigger(self, value=""):
		print("Check alerts local")
		if self.host.config._get('location', "") != "":
			location = self.host.config._get('location', "")
		else:
			return self.message("No location found. 'set location to x'")
		
		if self.host.config._get('weather_token', "") != "":
			pass
		else:
			return self.message("An API token for Darksky is required for the weather module. Check their website, get a token, then 'set weather_token to your_token'")

		location_arg = location	

		if " " in location:
			location = location.replace(" ", "+")
		
		res = requests.get(f"http://photon.komoot.de/api/?q={location}").text
		gl = json.loads(res)
		
		if len(gl['features']) == 0:
			return self.message("Problem looking up that location")
			
		lat = gl['features'][0]['geometry']['coordinates'][1]
		lng = gl['features'][0]['geometry']['coordinates'][0]
		
		try:
			city = 	gl['features'][0]['properties']['city']	
		except:
			city = 	gl['features'][0]['properties']['country']	

		weather = forecast(self.host.config._get('weather_token'), lat, lng)

		if weather is None:
			return self.message("No data found.")
		s = ""	
		try:
			for item in weather.alerts:
				s += f"{item.title}\n{item.description}\n\n"
			
			return self.message(s)
		except AttributeError:
			return self.message(f"No alerts for {city}.")
	
class WeatherAlertOtherCheck(commands.BaseCommand):
	def __init__(self, host):
		super().__init__(host)
		self.addListener("show me weather alerts for")
		self.addListener("show the weather alerts for")
		self.inter = True
		
	def onTrigger(self, value=""):
		print(f"Check alerts remote {value}")
		if self.host.config._get('weather_token', "") != "":
			pass
		else:
			return self.message("An API token for Darksky is required for the weather module. Check their website, get a token, then 'set weather_token to your_token'")

		location = value
		location_arg = location	

		if " " in location:
			location = location.replace(" ", "+")
		
		res = requests.get(f"http://photon.komoot.de/api/?q={location}").text
		gl = json.loads(res)
		
		if len(gl['features']) == 0:
			return self.message("Problem looking up that location")
			
		lat = gl['features'][0]['geometry']['coordinates'][1]
		lng = gl['features'][0]['geometry']['coordinates'][0]
		
		try:
			city = 	gl['features'][0]['properties']['city']	
		except:
			city = 	gl['features'][0]['properties']['country']	

		weather = forecast(self.host.config._get('weather_token'), lat, lng)

		if weather is None:
			return self.message("No data found.")
	
		s = ""	
		try:
			for item in weather.alerts:
				s += f"{item.title}\n{item.description}\n\n"
			
			return self.message(s)
		except AttributeError:
			return self.message(f"No alerts for {city}.")
	
	
	
	
