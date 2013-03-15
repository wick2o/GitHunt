#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import curses.ascii

halt = False
try:
	import betterwalk
except:
	print 'Missing needed module: easy_install betterwalk'
	halt = True
try:
	import argparse
except:
	print 'Missing module: easy_install argparse'
	halt = True
try:
	import sqlite3
except:
	print 'Missing module: easy_install sqlite3'
	halt = True
try:
	import curses.ascii
except:
	print 'Missing module: curses'
	halt = True
if halt == True:
	sys.exit()

def setup():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--database', action='store', dest='database', required=True, help='database to use')
	parser.add_argument('-f','--folder', action='store', dest='folder', required=True,help='Base path')
	parser.add_argument('-m','--multi', action='store', dest='multi', default=1, type=int, help='multiple loops')
	global args
	args = parser.parse_args()

def extractStrings(fileName):
	frag=""
	strList=[]
	bufLen=2048
	FRAG_LEN=4 # Min length to report as string
	fp=open(fileName, "rb")
	offset=0
	buf=fp.read(bufLen)
	while buf:
		for char in buf:
			# Uses curses library to locate printable chars
			# in binary files.
			if curses.ascii.isprint(char)==False:
				if len(frag)>FRAG_LEN:
					strList.append([hex(offset-len(frag)),frag])
					frag=""
				else:
					frag=frag+char
					offset+=1
					buf=fp.read(bufLen)
	return strList

def main():
	setup()
	
	if os.path.exists(args.database):
		db = sqlite3.connect(args.database)
		c = db.cursor()
		c.execute("PRAGMA default_cache_size=900000")
		c.execute("PRAGMA cache_size=900000")
		c.execute("PRAGMA synchronous = OFF")
		c.execute("PRAGMA journal_mode = OFF")
		c.execute("PRAGMA locking_mode = EXCLUSIVE")
		c.execute("PRAGMA temp_store = MEMORY")
		c.execute("PRAGMA count_changes = OFF")
		c.execute("PRAGMA PAGE_SIZE = 4096")
		c.execute("PRAGMA compile_options") 
		c.execute('SELECT username,name,id FROM projects WHERE processed = 0 LIMIT %s' % (args.multi))
		
		res = c.fetchall()
		if len(res) == 0:
			print 'nothing to analyize'
		m_count = 0
		for i in res:
			my_path = os.path.join(args.folder,i[0],i[1])
			for r,d,f in betterwalk.walk(my_path):
				for file in f:
					# POPULATE files table
					#print file
					c.execute("SELECT count(name) FROM files WHERE name = '%s'" % (file.replace("'", '')))
					res = c.fetchall()
					if res[0][0] == 0:
						c.execute("INSERT INTO files (name) values ('%s')" % (file.replace("'", '')))
					else:
						c.execute("UPDATE files SET count = count + 1 WHERE name = '%s'" % (file.replace("'", '')))
					
				for dir in d:
					# POPULATE dirs table
					#print dir
					c.execute("SELECT count(name) FROM dirs WHERE name = '%s'" % (dir.replace("'", '')))
					res = c.fetchall()
					if res[0][0] == 0:
						c.execute("INSERT INTO dirs (name) values ('%s')" % (dir.replace("'", '')))
					else:
						c.execute("UPDATE dirs SET count = count + 1 WHERE name = '%s'" % (dir.replace("'", '')))
				
			m_count += 1		
			c.execute("UPDATE projects SET processed = '1' WHERE username = '%s' AND name = '%s'" % (i[0], i[1]))
			db.commit()
			print '%s: Completed username: %s and project: %s' % (m_count, i[0],i[1])
			
		try:
			c.close()
		except:
			pass
		
		db.close()

	else:
		print 'Database does not exist...'
		sys.exit()
	
if __name__ == "__main__":
	main()
	
	