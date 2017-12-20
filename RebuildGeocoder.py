# This script rebuilds the geocoders with the current state of the feature classes


####Methods####
import urllib, urllib2, json
import arcpy
communication = ""


def gentoken(server, adminUser, adminPass, expiration=60):
	#Re-usable function to get a token required for Admin changes
	
	query_dict = {'username':   adminUser,
				  'password':   adminPass,
				  'expiration': str(expiration),
				  'client':     'requestip'}
	
	query_string = urllib.urlencode(query_dict)
	url = "http://{}/arcgis/admin/generateToken".format(server)
	
	token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())
	#print token
		
	if "token" not in token:
		print "token['messages']"
		quit()
	else:
		return token['token']


def stopStartServices(server, adminUser, adminPass, stopStart, serviceList, token=None):  
	''' Function to stop, start or delete a service.
	Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
	stopStart = Stop|Start|Delete
	serviceList = List of services. A service must be in the <name>.<type> notation
	If a token exists, you can pass one in for use.  
	'''    
	print stopStart
	communication = ""
	
	# Get and set the token
	if token is None:       
		token = gentoken(server, adminUser, adminPass)
	
	# Getting services from tool validation creates a semicolon delimited list that needs to be broken up
	services = serviceList.split(';')
	
	# Modify the services(s)    
	for service in services: 
		service = urllib.quote(service.encode('utf8'))
		try:
			op_service_url = "http://{}/arcgis/admin/services/{}/{}?token={}&f=json".format(server, service, stopStart, token)
		except:
			communication = communication + "\n Error for "+service+" "+str(arcpy.GetMessages())
			print op_service_url
		try:
			status = urllib2.urlopen(op_service_url, ' ').read()
			if 'success' in status:
				print service + " ==== " + stopStart
				communication = communication + '\n\n' +service + " ==== " + stopStart
			else:
				communication = communication+"\n "+stopStart+" Error for "+service+" Status: "+ status
		except:
			communication = communication + "\nNo status to report "+service
	
	return communication
###############

def RebuildGeocoder():
	return communication
	
subject = ""
# Import system modules
import os, subprocess 
from arcpy import env
env.workspace = "\\vm-nt-gisdata1\MXDs\Locators"
print "workspace"


try:
	# define geocoder variables
	server = "" #server name
	adminUser =  ""
	adminPass =  ""
	serviceList = ""  #list of geocoders to rebuild. Seperate service names with ";".
	pathGeocoders = ""  #folder path where geocoding services are located
	urlREST = "" #add the url to the rest endpoint services
	
	
	try:
		# Stop geocoders
		stopStart =  "Stop"
		communication = communication + stopStartServices(server, adminUser, adminPass, stopStart, serviceList)
		
		try:
			#### Rebuild ####
			# separate service list
			services = serviceList.split(';')

			for service in services: #iterate through each service
				# Separate geocoder name
				i = service.index('.')
				geocodeName = service[:i]
				print geocodeName

				# Rebuild geocoder
				arcpy.RebuildAddressLocator_geocoding(pathGeocoders + geocodeName)
				print "rebuilt "+ geocodeName
				communication = communication + "\nRebuilt "+ geocodeName
			
			try:
				# Restart geocoder
				stopStart = "Start"
				communication = communication + stopStartServices(server, adminUser, adminPass, stopStart, serviceList)
				
			except:
				communication = communication + "\nFailed to restart geocoders"
		except:
			communication = communication + "\nFailed to rebuild geocoders"
	except:
		communication = communication + "\nFailed to stop geocoders"
	print "End"

except:
	communication = communication + " Stop and Rebuild Failed " + str(arcpy.GetMessages())

if "Failed" in communication:
	# Restart geocoder there was any error in the script so that the service is always re-started at end of script
	stopStart = "Start"
	for service in services:
		try:
			communication = communication + stopStartServices(server, adminUser, adminPass, stopStart, service)
		except:
			communication = communication + "Failed to start "+service

try:
	# Check if geocoders actually start
	for service in services:
		shortName = service[:service.index('.')]
		opener = urllib.FancyURLopener({})
		f = opener.open(urlREST + shortName +"/GeocodeServer?wsdl") 
		code = urllib.urlopen(urlREST + shortName +"/GeocodeServer?wsdl?wsdl").getcode()
		if code == 200:
			communication = communication + "\n" + shortName+" Officially Started"			
		else:
			communication = communication + "\nMessage: " +shortName+ " failed to start\n"
			subject = subject + shortName+" failed to start. "
except:
	communication = communication + "\nFailed to check geocoder start"
			
# Define the subject line of the email
if len(subject) == 0: #If there were no errors encountered
	subject = "Geocoder script ran normally"
else: #Means error WAS encountered
	# I want to know immediately if errors are encountered so I made a special behavior rule in Microsoft Outlook. To initiate this rule, I add "MES" to the subject
	subject = subject +"MES " #MES (important for Microsoft Outlook rule)

# Email when finished. Useful for scheduled scripts that don't output print commands
import smtplib, time, datetime, os

# Get the current time
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

# Add date
communication = st +"\n"+ communication
f = open("C:\Scripts\RebuildGeocoder.txt",'w')
f.seek(0)
f.write(communication)
f.close()

# Define sender and receivers
sender = '' #email address
receivers = ['']

# Define message variables
receiverStg = ""
length = len(receivers)
receiverUno = receivers[0]

# Test if there is only one receiver
if length == 1:
	receiverStg = receiverUno[:receiverUno.index('@')] + """ <"""+receiverUno+""">"""
# Then there must be multiple receivers, add each name to the string
else: 
	for receiver in receivers:
		receiverStg = receiverStg + receiver[:receiver.index('@')] + """ <"""+receiver+""">, """
	receiverStg = receiverStg[:-2]

message = """From: """ + sender[:sender.index('@')] + """ <"""+sender+""">
To: """+receiverStg+"""
Subject:"""+subject+"""

The Rebuild Geocoder Script was run at.  """ + st + """ from """ + os.environ['COMPUTERNAME'] + """.

""" + communication + """ 

"""

# Send Email
try:
   smtpObj = smtplib.SMTP('') #Need bounce string such as bounce.org.oh.us
   smtpObj.sendmail(sender, receivers, message)         
   print "Successfully sent email"
except SMTPException:
   print "Error: unable to send email"
   communication = communication + "\nUnable to send email"
 
