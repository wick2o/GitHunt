#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

halt = False
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
if halt == True:
	sys.exit()

def setup():
	parser = argparse.ArgumentParser()
	parser.add_argument('-d','--database', action='store', dest='database', required=True, help='database to use')
	parser.add_argument('-f','--folder', action='store', dest='folder', required=True,help='Base path')
	parser.add_argument('-m','--multi', action='store', dest='multi', default=1, type=int, help='multiple loops')
	global args
	args = parser.parse_args()

def main():
	setup()
	
	if os.path.exists(args.database):
		db = sqlite3.connect(args.database)
		c = db.cursor()
		c.execute('SELECT username,name FROM projects WHERE processed = 0 LIMIT %s' % (args.multi))
		
		res = c.fetchall()
		if len(res) == 0:
			print 'nothing to analyize'
		for i in res:
			my_path = os.path.join(args.folder,i[0],i[1])
			for r,d,f in os.walk(my_path):
				for file in f:
					c.execute("SELECT count(name) FROM files WHERE name = '%s'" % (file.replace("'", '')))
					res = c.fetchall()
					if res[0][0] == 0:
						c.execute("INSERT INTO files (name) values ('%s')" % (file.replace("'", '')))
					else:
						c.execute("SELECT count FROM files WHERE name = '%s'" % (file.replace("'", '')))
						res = c.fetchall()
						total = res[0][0] + 1
						c.execute("UPDATE files SET count = '%s' WHERE name = '%s'" % (total, file.replace("'", '')))
				
				for dir in d:
					c.execute("SELECT count(name) FROM dirs WHERE name = '%s'" % (dir.replace("'", '')))
					res = c.fetchall()
					if res[0][0] == 0:
						c.execute("INSERT INTO dirs (name) values ('%s')" % (dir.replace("'", '')))
					else:
						c.execute("SELECT count FROM dirs WHERE name = '%s'" % (dir.replace("'", '')))
						res = c.fetchall()
						total = res[0][0] + 1
						c.execute("UPDATE dirs SET count = '%s' WHERE name = '%s'" % (total, dir.replace("'", '')))
				
					
			print 'Completing username: %s and project: %s' % (i[0],i[1])
			c.execute("UPDATE projects SET processed = '1' WHERE username = '%s' AND name = '%s'" % (i[0], i[1]))
		db.commit()
			
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
	
	