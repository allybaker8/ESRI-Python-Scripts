## This script populates blank text field with next incremental ID


def IncrementIDText():
	return communication_Action

# Import system modules
import arcpy
import pyodbc
print "arcpy and pyodbc loaded"

# Set the Database Connection
db = "GEODATA@MGUPvGIS.sde"

# Set the username of a person that has ArcGIS desktop installed on the computer running this script- must have the connection file listed below 
user = "" #enter user name as text element

# Set the administrative workspace
arcpy.env.workspace = "C:\\Users\\" + user + "\\AppData\\Roaming\\ESRI\\Desktop10.3\\ArcCatalog\\" + db
arcpy.env.overwriteOutput = True
print "workspace loaded"

# Connect to the SQL server
con = pyodbc.connect(DRIVER="SQL Native Client 10.0",DSN)
cur = con.cursor()
##not used right now but in case we didn't want to hard code the SQL Queries
#fil = open('C:\\Scripts\\Test\\selectMax.sql','r')
#sqlFile = fil.read()
#fil.close()

# Define field name that will be populated. Must be text field containing numbers
fieldName = "" #Input field name here

# Define code to increment field
codeblock = """rec=0 \ndef autoIncrement(): \n\tglobal rec \n\tpStart ={} \n\tpInterval = 1 \n\tif (rec == 0): \n\t\trec = pStart \n\telse: \n\t\trec += pInterval \n\treturn rec"""
expression = "autoIncrement()"

# Declare misc variables
fcArray = []
communication_Action =  ""  #Communication of what the script accomplished
communication_Error = ""  #Communication of what errors the script encountered

# Open log file to record progress
f = open("C:\Scripts\IncrementIDText.txt",'w')
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
f.write(st)

print "entering try"
# Iterate through MXD and layers to populate blanks found in the inputed field
try:
	mapDocs = [] #Input MXD paths here
	for mapDoc in mapDocs:
		mxd = arcpy.mapping.MapDocument(mapDoc)
		f.write('\n\nMXD:' + mapDoc[(mapDoc.rfind('\\')+1):])
		lyrs = arcpy.mapping.ListLayers(mxd)
		for lyr in lyrs:
			if not lyr.isGroupLayer:  #exclude group layers, dataset
				# Isolate the feature class name from the data source
				try:
					s1 = lyr.dataSource
					s2 = '\\'
					s3 = s1.rfind(s2)
					fc = s1[(s3)+ len(s2):]
					print "\n" + fc + " starting"
					f.write("\n" + fc + " starting.")
					
					# Layers reference duplicate feature classes, skip over feature classes that have already been run
					if fc not in fcArray:
						fcArray.append(fc)
						#Make sure the input field exists in feature class
						if len(arcpy.ListFields(fc,fieldName)) > 0:
						
							# Make a layer from the feature class
							arcpy.MakeFeatureLayer_management(fc , "fcLayer")
							#print fc, "layer made"
							
							try:
								# Change the feature class name to format Name_Name
								fcSQL =fc[fc.rindex('.')+1:]
								# Define SQL Queries
								sqlQueries = ["""USE [GEODATA];\n    \n    DECLARE\t@return_value int;\n\n
								EXEC\t@return_value = [sde].[set_current_version]\n\t\t\t@version_name = N'GIS';
								\n\n;""","""SELECT name FROM GEODATA.sys.views WHERE name LIKE '"""+fcSQL+"""%';"""]
								try:
									# Defines database and version
									cur.execute(sqlQueries[0])
									#print "command 0" #The first command is fun from array position 0
									# Select all view names that are candidates for this feature class's view table
									curViewName = cur.execute(sqlQueries[1])
									viewNameArrayRaw = curViewName.fetchall()
									
									# Eliminate unnecessary characters from view table names
									viewNameArray = []
									for viewName in viewNameArrayRaw:
										viewName = str(viewName)
										viewName = viewName[3:viewName.index(',')-1]
										viewNameArray.append(viewName)
									try:	
										# Pick the correct view name option. If views are named differently, add elif case for each view naming convention
										if len(viewNameArray) == 1:
											viewNameOne = viewNameArray[0]
										elif any(x in [fcSQL.lower()+"_VW" , fcSQL.upper()+"_VW" , fcSQL.title()+"_VW" , fcSQL+"_VW"] for x in viewNameArray):
											viewNameOne = fcSQL+"_VW"
										elif any(x in [fcSQL.lower()+"_evw" , fcSQL.upper()+"_evw" , fcSQL.title()+"_evw" , fcSQL+"_evw"] for x in viewNameArray):
											viewNameOne = fcSQL+"_evw"
										else:
											#print "View Name match not found: ", viewNameArray
											communication_Error = communication_Error + "\nView Name match not found: "+ viewNameArray
											f.write("\nView Name match not found: "+ viewNameArray)
										#print "viewNameOne ",viewNameOne
										
									
										try:
											if viewNameOne: # Checks if View Name was selected
												f.write("\nView Name Selected:"+viewNameOne)
												# Run select max ID query
												sqlSelectMax = """SELECT(SELECT MAX(CAST("""+viewNameOne+"""."""+fieldName+""" as INT)) as
												"""+viewNameOne[:viewNameOne.rindex('_')]+"""\n    FROM \n\t    GIS."""+viewNameOne+""");"""
												curRes = cur.execute(sqlSelectMax)
												#print "command 1"
												
												# Fetch max and convert to next Field int
												maxStr = str(curRes.fetchone()) #Format is '(None, )'
												maxfacID = maxStr[1:maxStr.index(',')]
												print "The maximum "+fieldName+" for " + fc + " is " + maxfacID
												f.write("\nThe maximum "+fieldName+" for " + fc + " is " + maxfacID)
												maxfacIDint = int(maxfacID) + 1
												#print "The next "+fieldName+"ID will be ", maxfacIDint
												
												try:
													# Select Featuers with no Field: [Field] IS NULL OR [Field] = '' OR [Field] = '0'
													arcpy.SelectLayerByAttribute_management("fcLayer", "NEW_SELECTION", " ["+fieldName+"] IS NULL ")
													arcpy.SelectLayerByAttribute_management ("fcLayer", "ADD_TO_SELECTION", " ["+fieldName+"] = '' ")
													arcpy.SelectLayerByAttribute_management ("fcLayer", "ADD_TO_SELECTION", " ["+fieldName+"] = '0' ")
													sr = int(arcpy.GetCount_management ("fcLayer").getOutput(0))
													print sr, "records selected in " + fc

													obIDVal = ["ObjectID"]
													for row in arcpy.SearchCursor("fcLayer"):
														obIDVal.append(str(row.objectid))
													f.write(str(obIDVal))
													
													if sr > 0: # Check that there are records selected
														# Execute CalculateField 
														arcpy.CalculateField_management("fcLayer", fieldName, expression, "PYTHON", codeblock.format(maxfacIDint))
														print "Blanks populated in " + fc
														communication_Action = communication_Action + "\nLayer " + fc + " had " + str(sr) + " records calculated.\n"
														f.write("\nLayer " + fc + " had " + str(sr) + " records calculated.\n")
													else:
														print "None selected in " + fc
														f.write("\n"+fc+" is good to go")
												except:
													print "Couldn't select or calculate any records in " + fc
													communication_Error = communication_Error + "\nLayer " + fc + " didn't get any new "+fieldName+" IDs but may need them."
													f.write("\nLayer " + fc + " didn't get any new "+fieldName+" IDs but may need them.")
											else:
												#print "No view name option selected"
												communication_Error = communication_Error + "\nNo view name option selected for "+fc
												f.write("\nNo view name option selected for "+fc)
										except:
											if maxfacID == "None":
												communication_Error = communication_Error + "\nNo features in "+fc
												f.write("\nNo features in "+fc)
											else:
												communication_Error = communication_Error + "\nProblem selecting Max "+fieldName+" ID in "+fc
												f.write("\nProblem selecting Max "+fieldName+" ID in "+fc + "\nSelect Query used: "+sqlSelectMax)
									except:
										communication_Error = communication_Error + "\nProblem choosing view name option for "+fc
										f.write("\nProblem choosing view name option for "+fc)
								except:
									communication_Error = communication_Error + "\nProblem with SQL queries of Pick Version or Get viewNameArray for "+fc
									f.write("\nProblem with SQL queries of Pick Version or Get viewNameArray for "+fc)
							except:
								communication_Error = communication_Error + "\nProblem with feature class name for "+fc
								f.write("\nProblem with feature class name for "+fc)
						else:
							print "No "+fieldName+", Dude in " + fc
							f.write("\nLayer " + fc + " doesn't have a "+fieldName+" field.")
				except:
					print "Fail in the layer portion of " + str(lyr)
					communication_Error = communication_Error + "\nProblem with the layer or data source for" + str(lyr) + " layer."
					#print arcpy.GetMessages()
					f.write("\nProblem with the layer or data source for" + str(lyr) + " layer.")
except:
	communication_Error = communication_Error + "\nProblem with MXD "+mapDoc
	f.write("\nProblem with MXD "+mapDoc)


if communication_Error:
	communication_Action= communication_Action + communication_Error

# Email when finished. Useful for scheduled scripts that don't output print commands
import smtplib, time, datetime, os

#Get the current time
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

# Define sender and receivers
sender = '' #Add email address. Such as name@org.oh.us
receivers = ['']  #Add email address

# Define message variables
receiverStg = ""
length = len(receivers)
receiverUno = receivers[0]

# Test if there is only one receiver for proper formating of email
if length == 1:
	receiverStg = receiverUno[:receiverUno.index('@')] + """ <"""+receiverUno+""">"""
# Therefore, there must be multiple receivers so add each name to the receiver string
else: 
	for receiver in receivers:
		receiverStg = receiverStg + receiver[:receiver.index('@')] + """ <"""+receiver+""">, """
	receiverStg = receiverStg[:-2]

message = """From: """ + sender[:sender.index('@')] + """ <"""+sender+""">
To: """+receiverStg+"""
Subject: Increment ID Text

The Increment ID Text Script was run at """ + st + """ from """ + os.environ['COMPUTERNAME'] + """.

""" + communication_Action + """ 

Get the ID?"""

# Send email
try:
   smtpObj = smtplib.SMTP('') #Need bounce string such as bounce.org.oh.us
   smtpObj.sendmail(sender, receivers, message)         
   print "Successfully sent email"
   f.write("\nSuccessfully sent email")
except SMTPException:
   print "Error: unable to send email"
   f.write("\nError, unable to send email")

print communication_Action

# Close the log file
f.close()
print "file closed"


