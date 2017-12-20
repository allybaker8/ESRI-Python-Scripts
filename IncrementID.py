
## This script finds the maximum number in a field and populates empty, blanks, or zeros with the sequential values incremented from the max. 
## With the current field varaibles, the script populates ADDR_ID and SEG_ID

## Developed by The City of Dublin


def AddressIDMax():
	return communication_Action	

# Import system modules
import arcpy
import pyodbc
print "arcpy and pyodbc loaded"

# Set the Database Connection
db = "" #add the database connection file

# Set the username of a person that has ArcGIS desktop installed on the computer running this script- must have the connection file listed below 
user = ''  #enter user name as text element

# Set the administrative workspace
arcpy.env.workspace = "C:\\Users\\" + user + "\\AppData\\Roaming\\ESRI\\Desktop10.3\\ArcCatalog\\" + db
arcpy.env.overwriteOutput = True
print "workspace loaded"

# Connect to the SQL server
con = pyodbc.connect(DRIVER="SQL Native Client 10.0",DSN)
cur = con.cursor()

# Code block to increment ID
codeblock = """rec=0 \ndef autoIncrement(): \n\tglobal rec \n\tpStart ={} \n\tpInterval = 1 \n\tif (rec == 0): \n\t\trec = pStart \n\telse: \n\t\trec += pInterval \n\treturn rec"""
expression = "autoIncrement()"

# Declare other misc variables
fcArray = []
maxfacID = ""
communication_Action =  "" #Communication of what the script accomplished
communication_Error = "" #Communication of what errors the script encountered

# Open log file to hold communication_Action and communication_Error
f = open("C:\LogFileName.txt",'w')
ts = time.time() #Used to timestamp when the script ran
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
f.write(st)

# Define feature class names that need fields populated
featureClass = ["MORPC_GEODATA.GIS.LBRSCENTERLINES_FRA", "MORPC_GEODATA.GIS.LBRSaddresspoints_Fra"]


try:
	# Match feature class name to its field name
	for fc in featureClass:
		if fc == "MORPC_GEODATA.GIS.LBRSCENTERLINES_FRA":
			fieldName = "SEG_ID"  #name of field with blanks or NULLs or zeros to be populated
		elif fc == "MORPC_GEODATA.GIS.LBRSaddresspoints_Fra":
			fieldName = "ADDR_ID"  #name of field with blanks or NULLs or zeros to be populated
		else:
			print "No field name match for this feature class: ", fc
			f.write("\nNo field name match for this feature class: "+fc)
			raise Exception
		print "\n" + fc + " starting"
		f.write("\n" + fc + " starting.")
		
		if fc not in fcArray:
			fcArray.append(fc)    # This line is a reminant from another script, kept for convenience
			# Make sure the field exists in the feature class
			if len(arcpy.ListFields(fc,fieldName)) > 0:
			
				# Make a layer from the feature class
				arcpy.MakeFeatureLayer_management(fc , "fcLayer")
				#print fc, "layer made"
				
				# In this section, use the maximum ID from the feature class's SQL view so the max number reflects the most recent edit to avoid assigning duplicate IDs
				try:
					# Change the feature class name to format Name_Name
					fcSQL =fc[fc.rindex('.')+1:]
					print "fcSQL ",fcSQL
					# Define SQL Query
					sqlQueries = ["""USE [MORPC_GEODATA];\n    \n    DECLARE\t@return_value int;""","""SELECT name FROM MORPC_GEODATA.sys.views WHERE name LIKE '"""+fcSQL+"""%';"""]
					try:
						# Query defines database and version
						cur.execute(sqlQueries[0])
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
							print "viewNameOne ",viewNameOne

							try:
								if viewNameOne: # Checks if View Name was selected
									f.write("\nView Name Selected:"+viewNameOne)
									# Set min and max range for that field
									if fieldName == "ADDR_ID":
										max = 2499999   # Valid High Range for the City of Dublin
										min = 2000000   # Valid Low Range for the City of Dublin
									elif fieldName == "SEG_ID":
										max = 249999    # Valid High Range for the City of Dublin
										min = 200000    # Valid Low Range for the City of Dublin
									else:
										print "No case found for this field name: ", fieldName
										f.write("No case found for this field name: "+fieldName)
										
									# Run select max ID query
									sqlSelectMax = """SELECT MAX("""+viewNameOne+"""."""+fieldName+""") as """+viewNameOne[:viewNameOne.rindex('_')]+"""\n    FROM \n\t    GIS."""+viewNameOne+""" WHERE GIS."""+viewNameOne+"""."""+fieldName+""" IN (SELECT """+fieldName+""" FROM GIS."""+viewNameOne+""" WHERE GIS_MAINT_AUTH = 2 AND """+fieldName+""" > """+str(min)+""" AND """+fieldName+""" < """+str(max)+""");"""
									curRes = cur.execute(sqlSelectMax)
									print "sql Select: ",sqlSelectMax
									
									# Fetch max and convert to next ID int
									maxStr = str(curRes.fetchone()) #Format is '(Decimal('#.#'), )'
									maxfacID = maxStr[maxStr.index("'")+1:maxStr.index('.')]
									print "The maximum "+fieldName+" for " + fc + " is " + maxfacID
									f.write("\nThe maximum "+fieldName+" for " + fc + " is " + maxfacID)
									maxfacIDint = int(maxfacID) + 1
									print "The next "+fieldName+" will be ", maxfacIDint
									
									try:
										# Select Features with no ID: [AddressID] IS NULL OR [AddressID] = 0
										arcpy.SelectLayerByAttribute_management("fcLayer", "NEW_SELECTION", " ["+fieldName+"] IS NULL  AND GIS_MAINT_AUTH =2")
										arcpy.SelectLayerByAttribute_management ("fcLayer", "ADD_TO_SELECTION", " ["+fieldName+"] = 0  AND GIS_MAINT_AUTH =2")
										sr = int(arcpy.GetCount_management ("fcLayer").getOutput(0))
										print sr, "records selected in " + fc

										# Check that there are records selected
										if sr > 0:
											# Keep record of all edit feature's Object IDs
											obAddID = ["ObjectID"]
											for row in arcpy.SearchCursor("fcLayer"):
												obAddID.append(str(row.objectid))
											f.write(str(obAddID))
											print obAddID
											# Execute CalculateField 
											arcpy.CalculateField_management("fcLayer", fieldName, expression, "PYTHON", codeblock.format(maxfacIDint))
											print "Blanks populated in " + fc
											communication_Action = communication_Action + "\nLayer " + fc + " had " + str(sr) +" "+ fieldName+" calculated."+str(obAddID)+"\n"
											f.write("\nLayer " + fc + " had " + str(sr) +" "+ fieldName +" calculated.\n")
										else:
											print "None selected in " + fc
											f.write("\n"+fc+" is good to go")
									except:
										print "Couldn't select or calculate any records in " + fc
										communication_Error = communication_Error + "\nLayer " + fc + " didn't get any new " +fieldName+" but may need them."
										f.write("\nLayer " + fc + " didn't get any new " +fieldName+" but may need them.")
									
								else:
									#print "No view name option selected"
									communication_Error = communication_Error + "\nNo view name option selected for "+fc
									f.write("\nNo view name option selected for "+fc)
							except  Exception, e:
								print e
								f.write("\nError: "+str(e))
								if maxfacID == "None":
									communication_Error = communication_Error + "\nNo features in "+fc
									f.write("\nNo features in "+fc)
								else:
									communication_Error = communication_Error + "\nProblem selecting "+fieldName+" in "+fc
									f.write("\nProblem selecting Max "+fieldName+" in "+fc + "\nSelect Query used: "+sqlSelectMax)
						except Exception, e:
							print e
							f.write("\nError: "+str(e))
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
				communication_Error = communication_Error + "\nLayer " + fc + " doesn't have a "+fieldName+" field."
				f.write("\nLayer " + fc + " doesn't have a "+fieldName+" field.")
except Exception:
	communication_Error = communication_Error + "\nProblem with feature class " + fc
	f.write("\nProblem with featureClass: "+fc)
	f.write("\nError: "+arcpy.GetMessages())

# If the script encountered an error then add communication_Error
if communication_Error:
	communication_Action= communication_Action + communication_Error

#Email when finished. Useful for scheduled scripts that don't output print commands
import smtplib, time, datetime, os

#Get the current time
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

# Define sender and receivers
sender = '' #Add email address. Such as name@org.oh.us
receivers = ['']  #Add email address
# If there were no duplicates found overwrite sender and receivers 
# This email step is unnecessary; I wanted to send an email to only myself the script ran but not send to others if nothing was accomplished
if not communication_Action:
	sender = ''  #Add email address
	receivers = ['']   #Add email address

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

# Define message body text
message = """From: """ + sender[:sender.index('@')] + """ <"""+sender+""">
To: """+receiverStg+"""
Subject: Increment ID Script 

The Increment ID Script was run at """ + st + """ from """ + os.environ['COMPUTERNAME'] + """.

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


