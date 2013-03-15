#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time

halt = False
try:
	import argparse
except:
	print 'Missing module: easy_install argparse'
	halt = True
try:
	import MySQLdb as mdb
except ImportError:
	print 'Missing needed module: easy_install MySQL-python'
	halt = True
if halt == True:
	sys.exit()

db_ip = '172.16.1.122'
db_user = 'root'
db_pass = 'toor'
db_name = 'gitdigger'


	
def setup():
	parser = argparse.ArgumentParser()
	parser.add_argument('-t','--table', action='store', dest='table', required=True,help='table to add data to')
	parser.add_argument('-f','--file', action='store', dest='file', required=True,help='file with items to add')
	
	global args
	args = parser.parse_args()


def main():
	setup()
	con = None
	
	f = open(args.file, 'r')
	words = f.readlines()
	f.close()
	
	try:
		con = mdb.connect(db_ip, db_user, db_pass, db_name)
		cur = con.cursor()
		
		
		for word in words:
			if word.strip() != "":
				cur.execute("INSERT INTO %s (name) VALUES ('%s') ON DUPLICATE KEY UPDATE count = count + 1" % (args.table, word.strip().replace("'", '')))
				con.commit()
				print 'added: %s...' % word.strip().replace("'", '')
		
	except mdb.Error, e:
		print 'Error %d: %s' % (e.args[0], e.args[1])
		sys.exit(1)
	finally:
		if con:
			con.close()
				
	
if __name__ == "__main__":
	main()
	
	