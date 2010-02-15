#!/usr/bin/env python
#
# oggtakeover.py by Sebastian Moors
# Licensend under GPL2
# Tool for converting many audio files to ogg using mp32ogg
# if called without arguments, the current folder will be converted to ogg vorbis (recursive)


#TODO: 1.REMOVE SLASHS AT END OF DIR / FILENAMES

import os
import sys
import re
import getopt
import sqlite
import shutil


VERSION="0.04"

class converter:
	'''virtual'''
	#A list of accepted input types, for example {"mp3"}
	acceptedTypes=[]
	name="Virtual converter"
	#path to converter programm
	path=""

	def convert(self,input,output):
		#convert input to output
		pass



class mp32ogg(converter):
	acceptedTypes=['mp3']
	path=""
	name="mp32ogg"

	def __init__(self):
		ShellObj = os.popen('/usr/bin/which mp32ogg','r')
		my_buffer=((ShellObj.read()).strip())
		if my_buffer=="":
			return false

	def convert(self,input,output):
		dirname=os.path.dirname(output)
		dirname=dirname.replace("'",r"'")
		command="cd \"%(oggPath)s\" && mp32ogg \"%(fname)s\" > /dev/null"  % {'fname':input, 'oggPath': dirname}
		print command
	        print "mp32ogg: converting %s" % input
		return os.system(command)

class dumbconverter(converter):

	acceptedTypes=['*']
	name="dumb"

	def convert(self,input,output):
		#just copy input to output
		shutil.copyfile(input,output)
		print "dumb: copying " + input + " to " + output
		return 0


class oggtakeover:

	def __init__(self):
		self.dbdir=os.path.expanduser("~/.oggtakeover")
		self.converterList=[]

		#Hash: extension => converter object
		self.extensionHash={}

		#initialise converter plugins
		mp32oggc=mp32ogg()
		if mp32oggc: self.converterList.append(mp32oggc)

		dumbc=dumbconverter()
		if dumbc: self.converterList.append(dumbc)



		for conv in self.converterList:
			for item in conv.acceptedTypes:
				if not self.extensionHash.has_key(item):
					self.extensionHash[item]=conv





	def connect(self):
		self.db = sqlite.connect(self.dbdir + "/meta.db")
		self.cursor = self.db.cursor()



	def createDatabase(self,mp3dir=".",oggdir="",dbdir="~/.oggtakeover",ffilter="mp3,jpg,txt",purge="n"):

		if ffilter=="":
			ffilter="mp3,jpg,txt"
		else:
			ffilter=ffilter

		self.dbdir=os.path.expanduser(dbdir)
		self.dbdir=os.path.realpath(self.dbdir)

		self.mp3dir=os.path.expanduser(mp3dir)
		self.mp3dir=os.path.realpath(self.mp3dir)

		if oggdir=="":
			self.oggdir=os.path.dirname(self.mp3dir) + "/ogg"
		else:
			self.oggdir=os.path.expanduser(oggdir)

		self.oggdir=os.path.realpath(self.oggdir)



		#default: create ogg folder at same hierachy as mp3 folder
		if not os.path.isdir(self.oggdir):
			os.mkdir(self.oggdir)




		if not os.path.isdir(self.dbdir):
			os.mkdir(self.dbdir)


		if os.path.isfile(self.dbdir + "/meta.db"):
			print "Exiting, Database already exists"
			sys.exit(0)



		#initialise sqlite database
		self.connect()

		sql="CREATE TABLE 'mp3files' (fileID INTEGER PRIMARY KEY, name TEXT,status TEXT)"
		self.cursor.execute(sql)

		sql="CREATE TABLE 'config' (key TEXT,value TEXT)"
		self.cursor.execute(sql)

		self.db.commit()


		#save config values to database
		#where are our input files ?
		sql="INSERT INTO 'config' VALUES ('%(key)s','%(value)s')" % {'key':"mp3dir",'value': self.mp3dir}
		self.cursor.execute(sql)


		#output directory
		sql="INSERT INTO 'config' VALUES ('%(key)s','%(value)s')" % {'key':"oggdir",'value': self.oggdir}
		self.cursor.execute(sql)
		self.db.commit()

		#filter
		sql="INSERT INTO 'config' VALUES ('%(key)s','%(value)s')" % {'key':"filter",'value': ffilter}
		self.cursor.execute(sql)
		self.db.commit()

		#filter
		sql="INSERT INTO 'config' VALUES ('%(key)s','%(value)s')" % {'key':"purge",'value': purge}
		self.cursor.execute(sql)
		self.db.commit()

		addedCounter=0

		#split up ffilter (comma-seperated) "mp3" or "mp3,jpg,wav"
		flist=ffilter.split(",")

		regexp = re.compile("(\.mp3)$",re.IGNORECASE)

		for root, dirs, files in os.walk(self.mp3dir):
			for name in files:
				#allow only *.mp3
				for ending in flist:
					if name.endswith(ending):
						fname=os.path.join (root,name)
						print "Adding %s to database" % fname
						status='n'

						self.cursor.execute("INSERT INTO 'mp3files' VALUES (NULL,%s,%s)",(fname,status))

						self.db.commit()
						addedCounter=addedCounter+1
		if addedCounter==0:
			#remove database
			os.remove(self.dbdir+"/meta.db")
			print "No matching Files found, no database was created"
		else:
			print "Database created, %i Files added" % addedCounter

	def convert(self,input,output):
		#check which converter is available for converting input to output
		#1. determine file type


		inputField=input.split("/")
		for a in inputField:
			a=re.escape(a)
		input="/".join(inputField)
		#print input
		ending=input[input.rfind(".")+1:]

		print "(" + str(self.actFile) + "/" + str(self.max) + ")",
		if self.extensionHash.has_key(ending):
			returnv= self.extensionHash[ending].convert(input,output)
		else:
			returnv= self.extensionHash["*"].convert(input,output)


		return returnv

	def work(self,dbdir):

		error=0

		self.dbdir=os.path.expanduser(dbdir)

		self.connect()

		sql="SELECT value FROM 'config' WHERE key='mp3dir'"
		self.cursor.execute(sql)
		row=self.cursor.fetchone()
		self.mp3dir=row[0]

		sql="SELECT value FROM 'config' WHERE key='oggdir'"
		self.cursor.execute(sql)
		row=self.cursor.fetchone()
		self.oggdir=row[0]

		sql="SELECT value FROM 'config' WHERE key='filter'"
		self.cursor.execute(sql)
		row=self.cursor.fetchone()
		self.filter=row[0]

		sql="SELECT value FROM 'config' WHERE key='purge'"
		self.cursor.execute(sql)
		row=self.cursor.fetchone()
		self.purge=row[0]


		sql="SELECT * FROM 'mp3files' WHERE status='n'"

		self.cursor.execute(sql)
		rows=self.cursor.fetchall()
		fname=""

		#filecount
		self.actFile=1

		#maxCount
		self.max=len(rows)
		for row in rows:
			fname=row[1]
			oggName=os.path.basename(fname)
			oggName.replace(".mp3",".ogg")
			oggPath=self.oggdir + os.path.dirname(fname.replace(self.mp3dir,"",1))

			if not os.path.isdir(oggPath): os.makedirs(oggPath)
			oggFile=oggPath + "/" + oggName
			retval=self.convert(fname,oggFile)
			if retval==0:
				if self.purge=="y":
					#delete converted file
					try:
						os.remove(fname)
					except OSError,e:
						"An error occured while removing %s",e
					print "Removing %s" % fname


				self.cursor.execute("UPDATE mp3files SET status= 'y' WHERE name= %s" , fname)
				self.db.commit()
			else:
				error=1
				print "Ooops, on error occured while converting %s" % fname

				#interupted, for example by ctrl+c
				if retval==256:
					sys.exit(0)
		
			self.actFile=self.actFile+1

		#remove empty directory after converting
		print fname
		if fname!="" and len(os.listdir(os.path.dirname(fname)))==0:
			os.rmdir(os.path.dirname(fname))



		if error==0:
			#All work is done, go home and delete the database
			print "\n Removing database" + self.dbdir+"/meta.db"
			os.remove(self.dbdir+"/meta.db")
def usage():
	print '''

To convert your audio collection to ogg vorbis, create a database with 
oggtakeover -c -i /inputdir -o outputdir 

If the purge option "-p" is set, all converted inputfiles will be deleted. 

Specify a filename filter with "-f" to convert only filename with a certain ending. 
Example:

oggtakeover -c -i /mp3 -o /ogg -f "mp3,wav" -p 

This example will create a database to convert any file ending with .mp3 or .wav located in /mp3 to /ogg. 
To convert these files, run oggtakeover without any arguments. 


Create a database with oggtakeover --create-database mp3dir 
Options: 
	 -h\tHelp
	 -c\tcreate database
	 -i\tinput directory
	 -o\toutput directory
         -d\tdatabase
	 -f\tfilter
         -p\tpurge	
'''
				






if __name__=="__main__":


	#
	# DEFAULT SETTINGS
	#


	#standart database directory
	dbdir="~/.oggtakeover"

	#where to look for input data
	indir=""
	outdir=""

	#--createDatabase
	create=0

	formatfilter=""

	#delete converted input files?
	#default: no
	purge="n"


	try:
		long_opts=["help","create-database","inputdir","outputdir","database=","filter=","purge"]
		opts, args = getopt.getopt(sys.argv[1:], "hci:o:d:f:p",long_opts )

	except getopt.GetoptError:
		# wrong options etc.
		# print help information and exit:
		usage()
		sys.exit(2)

	for option, argument in opts:
		if option in ("-h", "--help"):
			usage()
			sys.exit()

		if option in ("-i","--inputdir"):
			indir=argument
		
		if option in ("-o","--outputdir"):
			outdir=argument
			


		if option in ("-f","--filter"):
			formatfilter=argument


		if option in ("-c","--create-database"):
			create=1

		if option in ("-d","--database"):
			dbdir=argument

		if option in ("-p","--purge"):
			purge="y"



	conv = oggtakeover()

	if create==1:
		if indir!="":
			conv.createDatabase(indir,ffilter=formatfilter,purge=purge)
		else:
			conv.createDatabase()
			sys.exit()
	else:


		dbdir=os.path.expanduser(dbdir)

		if os.path.isfile(dbdir + "/meta.db"):
			print "\noggtakeover Version %s by Sebastian Moors" % VERSION
			print "Licensed under GPL2 \n"
			conv.work(dbdir)
		else:

			print "There's no database at " + dbdir + "\n"





