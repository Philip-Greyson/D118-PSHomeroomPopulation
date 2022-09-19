# importing module
import oracledb
import sys
import datetime
import os
from datetime import *

un = 'PS' #PSNavigator is read only, PS is read/write
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD') #the password for the PSNavigator account
cs = os.environ.get('POWERSCHOOL_PROD_DB') #the IP address, port, and database name to connect to

print("Username: " + str(un) + " |Password: " + str(pw) + " |Server: " + str(cs)) #debug so we can see where oracle is trying to connect to/with
badnames = ['USE','TEST','TESTSTUDENT','TEST STUDENT','TESTTT','TESTT','TESTTEST']

with oracledb.connect(user=un, password=pw, dsn=cs) as con: # create the connecton to the database
	with con.cursor() as cur:  # start an entry cursor
		with open('Homerooms.csv', 'w') as outputfile:  # open the output file
			print("Connection established: " + con.version)
			print('ID,Last,First,Internal ID,School,Status,Grade,New Homeroom,Old Homeroom', file=outputfile) #print header line in output file

			try:
				outputLog = open('Homeroom_log.txt', 'w') #open a second file for the log output

				cur.execute('SELECT student_number, first_name, last_name, id, schoolid, enroll_status, home_room, grade_level, dcid FROM students ORDER BY student_number DESC')
				rows = cur.fetchall() #fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
				today = datetime.now() #get todays date and store it for finding the correct term later
				# print("today = " + str(today)) #debug

				for entrytuple in rows: #go through each entry (which is a tuple) in rows. Each entrytuple is a single employee's data
					try:
						print(entrytuple) #debug
						entry = list(entrytuple) #convert the tuple which is immutable to a list which we can edit. Now entry[] is an array/list of the student data
						#for stuff in entry:
							#print(stuff) #debug
						if not str(entry[1]) in badnames and not str(entry[2]) in badnames: #check first and last name against array of bad names, only print if both come back not in it
							homeroom = "" #reset back to blank each user until we actually find info for them
							idNum = int(entry[0]) #what we would refer to as their "ID Number" aka 6 digit number starting with 22xxxx or 21xxxx
							firstName = str(entry[1])
							lastName = str(entry[2])
							internalID = int(entry[3]) #get the internal id of the student that is referenced in the classes entries
							schoolID = str(entry[4])
							status = str(entry[5]) #active on 0 , inactive 1 or 2, 3 for graduated
							currentHomeroom = str(entry[6]) if entry[6] else ""
							grade = int(entry[7])
							stuDCID = str(entry[8])
							

							if(status == "0"): #only worry about the students who are active, otherwise wipe out their homeroom
								#do another query to get their classes, filter to just the current year and only course numbers that contain HR
								try:
									cur.execute("SELECT id, firstday, lastday, schoolid FROM terms WHERE IsYearRec = 1 AND schoolid = " + schoolID + " ORDER BY dcid DESC") #get a list of terms for the school, filtering to only full years
									terms = cur.fetchall()
									for termTuple in terms: #go through every term
										# print(termTuple) #debug
										termEntry = list(termTuple)
										if ((termEntry[1] - timedelta(days = 14) < today) and (termEntry[2] + timedelta(days = 14) > today)): #compare todays date to the start and end dates with 2 week leeway so it populates before the first day of school
											termid = str(termEntry[0])
											#print("Found good term: " + termid)
									if grade < 0: #if they are a pre-k kid, we just take whatever course they are enrolled in
										cur.execute("SELECT course_number, teacherid, sectionid FROM cc WHERE studentid = " + str(internalID) + " AND termid = " + termid + " ORDER BY course_number")
									else: #for k-12, we want to search for a HR section
										cur.execute("SELECT course_number, teacherid, sectionid FROM cc WHERE instr(course_number, 'HR') > 0 AND studentid = " + str(internalID) + " AND termid = " + termid + " ORDER BY course_number")
									userClasses = cur.fetchall()
									if userClasses: #only overwrite the homeroom if there is actually data in the response
										for tuples in userClasses:
											classEntry = list(tuples) #convert the tuple which is immutable to a list which we can edit. Now classEntry[] is an array/list of the student courses
											courseID = str(classEntry[0])
											if (courseID != "CHR" and courseID != "IREADY"):
												teacherID = str(classEntry[1]) #store the unique id of the teacher
												sectionID = str(classEntry[2]) #store the unique id of the section, used to get classroom number later
												#print("ID: " + str(idNum) + " |ClassID: " + courseID + " |teacherID: " + teacherID, file=outputLog)
											else: #debug
												print("ID: " + str(idNum) + " |Found bad class: " + courseID, file=outputLog) #debug
										#once we have gone through all possible classes and found the "correct" one, use that info to get teacher name
										cur.execute("SELECT users_dcid FROM schoolstaff WHERE id = " + teacherID) #get the user dcid from the teacherid in schoolstaff
										schoolStaffInfo = cur.fetchall()
										teacherDCID = str(schoolStaffInfo[0][0]) #just get the result directly without converting to list or doing loop
										cur.execute("SELECT lastfirst FROM users WHERE dcid = " + teacherDCID)
										teacherName = cur.fetchall()
										homeroom = str(teacherName[0][0])
										#now that we found the homeroom and teacher name, also get the room number
										cur.execute("SELECT room FROM sections WHERE id = " + sectionID) #get the room number assigned to the sectionid correlating to our home_room
										roomNumber = cur.fetchall()
										homeroom_number = str(roomNumber[0][0])
										cur.execute("SELECT homeroom_number FROM u_studentsuserfields WHERE studentsdcid = " + stuDCID) #fetch their current homeroom number for comparison
										oldRoomNumber = cur.fetchall()
										currentHomeroom_number = str(oldRoomNumber[0][0]) if oldRoomNumber[0][0] else ""
										print("ID: " + str(idNum) + " |ClassID: " + courseID + " |teacherID: " + teacherID + " |sectionID: " + sectionID + " |Teacher Name: " + homeroom + " |Room Number: " + homeroom_number, file=outputLog)
								except Exception as err:
									print('Error on ' + str(idNum) + ': ' + str(err))
									print('Error on ' + str(idNum) + ': ' + str(err), file=outputLog)

							#else:
								#print("Skipping student due to not being active") #debug
							print(str(idNum)+','+lastName+','+firstName+','+str(internalID)+','+schoolID+','+status+','+str(grade)+',"'+homeroom+'","'+currentHomeroom+'"', file=outputfile) #outputs to the actual file
							#cur.execute("UPDATE students SET home_room = '" + homeroom + "' WHERE student_number = " + str(idNum)) #write the homeroom name to the student table
							#cur.execute("UPDATE u_studentsuserfields SET homeroom_number = '" + homeroom_number + "' WHERE studentsdcid = " + stuDCID) #write the homeroom number to the custom student user fields table
							#con.commit() #actually commit the changes to the database

							if (status == "0" and (homeroom != currentHomeroom) and currentHomeroom != ""):
								if (homeroom == ""):
									print("Severe mismatch on " + str(idNum) + ", Old: " + currentHomeroom + " | New: " + homeroom, file=outputLog)
								else:
									print("Mismatch on " + str(idNum) + ", Old: " +
										currentHomeroom + " | New: " + homeroom, file=outputLog)

							if (status == "0" and (homeroom_number != currentHomeroom_number) and currentHomeroom_number != ""):
								if (homeroom_number == ""):
									print("Homeroom number severe mismatch on " + str(idNum) + ", Old: " + currentHomeroom_number + " | New: " + homeroom_number, file=outputLog)
								else:
									print("Homeroom number mismatch on " + str(idNum) + ", Old: " + currentHomeroom_number + " | New: " + homeroom_number, file=outputLog)

					except Exception as err:
						print('Unknown Error on ' + str(entrytuple[0]) + ': ' + str(err))
						print('Unknown Error on ' + str(entrytuple[0]) + ': ' + str(err), file=outputLog)


			except Exception as er:
				print('Unknown Error: '+str(er))
				print('Unknown Error: '+str(er), file=outputLog)


