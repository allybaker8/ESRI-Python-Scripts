
##   This script removes duplicate IDs from chosen fields. It assigns a blank value to all duplicate features while retaining the original record(with the lowest ObjectID).


def RemoveDuplicates():
	# ENTER FIELD NAME HERE:  Must be text data type field containing numbers
	fieldName = "FacilityID"

	# Open a file to log progress
	c = open("C:\Scripts\RemoveDuplicateID.txt",'w')

	# Get the current time	
	import smtplib, time, datetime, os
	ts = time.time()
	st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
	c.write(st)

	# Import arcpy and numpy modules
	import arcpy
	import numpy

	# Local variables:
	Layer = "GIS.Layer"
	Free = "in_memory\\Free"

	# Declare other misc variables
	featureClassArray = []
	communication_Action = ""
	communication_Error = ""

	# Declare User and Database Variables
	user = "" #database user name
	db = "" #database connection name

	# Set the workspace
	arcpy.env.workspace = "C:\\Users\\" + user + "\\AppData\\Roaming\\ESRI\\Desktop10.3\\ArcCatalog\\" + db


	# Set up mxd list
	mapDocs = [] #array of mxd paths that the script will check the input field name in every included layer. Format: [r'\\path\Name.mxd',r'\\path\Name.mxd']

	for mapDoc in mapDocs: #loop through mxds
		c.write("\n" + mapDoc)
		try:
			mxd = arcpy.mapping.MapDocument(mapDoc)
			print "MXD", mapDoc	
			try:
				lyrs = arcpy.mapping.ListLayers(mxd)
				# Extract feature class name from layer data source
				for lyr in lyrs:
					s1 = lyr.dataSource
					s2 = '.sde\\'
					featureClass = s1[s1.index(s2) + len(s2):]
					
					# Check if feature class is in a dataset and eliminate if True
					if featureClass.find('\\') > 0:
						featureClass = featureClass[featureClass.index('\\') + len('\\'):]

					# Make short feature class name without database and version
					featureClassName = featureClass[featureClass.index('GEODATA.GIS.') + len('GEODATA.GIS.'):]

					try:
						if arcpy.Exists(Layer):
							# Delete old layer
							arcpy.Delete_management(Layer)

						if featureClass not in featureClassArray: #Checks if feature class was already run through in script, good exclusion process for mxds with multiple layers pointing to the same feature class
							featureClassArray.append(featureClass) #Add layer to array
							c.write("\nOpened "+featureClassName)
							print featureClassName
							try:
								# Make Feature Layer
								arcpy.MakeFeatureLayer_management(featureClass, Layer)
								try:
									if arcpy.Exists(Free):
										# Delete old table
										arcpy.Delete_management(Free)

									try:	
										if len(arcpy.ListFields(featureClass,fieldName)) > 0:
											# Process: Frequency
											arcpy.Frequency_analysis(Layer, Free, fieldName, "")
											try:
												# Define arrays to hold teh defined field ID
												arrfaq = []
												arrfac = []

												# Search for duplicate IDs
												cursor = arcpy.SearchCursor(Free)
												for row in cursor:
													fre = row.getValue('FREQUENCY') #Read frequency of each ID number
													fac = row.getValue(fieldName) #Read the ID number
													# Test for Null to replace fac with string
													if fac == None:
														fac = "NULL"
													if fre > 1: #Evaluates as True if there are duplicates
														arrfaq.append(fac) #Add the duplicate ID to the array
														c.write("\n"+fac+" appended")
												print "Duplicates: ",arrfaq

												for item in arrfaq: #For each duplicate ID
													# Clean up the text ID for calculation
													string = str(item) 
													newstr = string.replace("u'","")
													newer = newstr.replace("',","")
													# These are the three conditions in another script for field popluation so it will populate these values, no need to blank out
													# item == "NULL" because compare text not actual Null value, item is from array not field
													if item == 'NULL' or item == '' or item == '0':
														print "pass"
														pass
													else:
														arrfac.append(newer)

												# Check if any duplicates were found
												if arrfac:
													communication_Action = communication_Action + "\n"+featureClassName+" Duplicates: "+str(arrfac)
												try:
													# Select duplicates to be calculated
													for item in arrfac:
														print item    
														ob = []
														c.write(item+" selected")
														arcpy.SelectLayerByAttribute_management(Layer, "NEW_SELECTION", fieldName+" =" + """'"""+item+"""'""") #Select all rows from original layer with the ID
														
														try:
															cursor = arcpy.da.SearchCursor(Layer, 'OBJECTID')
															for row in cursor:
																ob.append(int(row[0])) #Read the object ID of all records that have that ID
															print ob
															c.write("\nobjectIDs: "+str(ob))
															try:
																# Remove the original record from the selection ie the record with the lowest object ID. 
																arcpy.SelectLayerByAttribute_management(Layer, "REMOVE_FROM_SELECTION", "OBJECTID = " + str(min(ob)))
																#c.write("\nlow objectid removed")
																sr = int(arcpy.GetCount_management (Layer).getOutput(0))
																print sr, "records selected in the ",featureClass
																print "lowest ID:",str(min(ob))
																c.write("\nlowest ID:"+str(min(ob)))
																#c.write("\ncount found")
																try:
																	# Blank out all duplicate values of that ID
																	arcpy.CalculateField_management (Layer, fieldName, '""', "PYTHON_9.3")
																	c.write("\n"+str(sr)+" records calculated")
																	#communication_Action = communication_Action+"\n"+str(sr)+" records calculated"
																	
																except:
																	c.write("\n" + "failed to calculate" + arcpy.GetMessages())
																	communication_Error = communication_Error + "\n" + "failed to calculate" + arcpy.GetMessages()
															except:
																c.write("\n" + "failed to unselect record with lowest object id" + arcpy.GetMessages())
																communication_Error = communication_Error + "\n" + "failed to unselect record with lowest object id" + arcpy.GetMessages()
														except:
															c.write("\n" + "failed to make object id array" + arcpy.GetMessages())
															communication_Error = communication_Error + "\n" + "failed to make object id array" + arcpy.GetMessages()
												except:
													c.write("\n" + "failed to select facility ids" + arcpy.GetMessages())
													communication_Error = communication_Error + "\n" + "failed to select facility ids" + arcpy.GetMessages()
												#print "done"
												c.write("\nfc done")
											except:
												c.write("\n" + "failed to make arrays" + arcpy.GetMessages())
												communication_Error = communication_Error + "\n" + "failed to make arrays" + arcpy.GetMessages()
										else:
											print "no "+fieldName
									except:
										c.write("\n" + "failed to make frequency table" + arcpy.GetMessages())
										communication_Error = communication_Error + "\n" + "failed to make frequency table" + arcpy.GetMessages()
								except:
									c.write("\n" + "failed to delete old frequency table" + arcpy.GetMessages())
									communication_Error = communication_Error + "\n" + "failed to delete old frequency table" + arcpy.GetMessages()
							except:
								c.write("\n" + "failed to make feature layer" + arcpy.GetMessages())
								communication_Error = communication_Error + "\n" + "failed to make feature layer" + arcpy.GetMessages()
					except:
						c.write("\n" + "failed to prepare layer" + arcpy.GetMessages())
						communication_Error = communication_Error + "\n" + "failed to prepare layer" + arcpy.GetMessages()
			except:
				c.write("\n" + "failed to define fc" + arcpy.GetMessages())
				communication_Error = communication_Error + "\n" + "failed to define fc" + arcpy.GetMessages()
		except:
			c.write("\n" + "failed to set up mxd" + arcpy.GetMessages())
			communication_Error = communication_Error + "\n" + "failed to set up mxd" + arcpy.GetMessages()
		

	print "really done"
	c.write("\nreally done")
	
	# Close the log file
	c.close()
	
	# If there was an error, add communication of the error to the communication that will be returned
	if communication_Error:
		communication_Action= communication_Action+communication_Error
	# If there were not any duplicates found
	elif not communication_Action:
		communication_Action = "There are no duplicates"
	
	# Add opening statement to communication_Action
	communication_Action = "\nDuplicate Remover: "+communication_Action
	
	return communication_Action

