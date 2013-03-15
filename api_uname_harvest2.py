#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import urllib
import urllib2
import socket
import base64
import time
import subprocess
import threading
import Queue
import shutil
import git
import datetime

halt = False

try:
	import argparse
except ImportError:
	print 'Missing needed module: easy_install argparse'
	halt = True

try:
	import simplejson as json
except ImportError:
	print 'Missing needed module: easy_install simplejson'
	halt = True

try:
	from git import *
except ImportError:
	print 'Missing needed module: easy_install gitpython'
	halt = True

try:
	import MySQLdb as mdb
except ImportError:
	print 'Missing needed module: easy_install MySQL-python'
	halt = True

if halt == True:
	sys.exit()

socket.setdefaulttimeout(120)

db_ip = '172.16.1.122'
db_user = 'root'
db_pass = 'toor'
db_name = 'gitdigger'

git_user = 'Riseed1985'
git_pass = 'eev8ieB9g'
git_limit = '5000'

hd_letter = 'M:'
hd_name = 'USB_HDD4'

def setup():
	parser = argparse.ArgumentParser()
	parser.add_argument('-m', '--mode', action='store', dest='mode', required=True, choices=['downloader','processor','grepper', 'test'], help='Choose Software Mode')

	global args
	args = parser.parse_args()
	
def dl_worker(itm):
	try:
		con = None

		o_path = '%s//%s' % (hd_letter, itm['path'])
		res = git.Git().clone(itm['clone_url'], o_path)

		try:
			con = mdb.connect(db_ip, db_user, db_pass, db_name)
			cur = con.cursor()
			cur.execute('INSERT INTO projects (username, name, harddrive) VALUES ("%s", "%s", "%s");\n' % (itm['path'].split('/')[0].strip(), itm['path'].split('/')[1].strip(), hd_name))
			con.commit()
		except mdb.Error, e:
			print 'Error %d: %s' % (e.args[0], e.args[1])
			sys.exit(1)
		finally:
			if con:
				con.close()

		print '%s\n' % res
	except:
		pass

def test():
	print 'running in test mode'
	try:
		cur = con.cursor()
		cur.execute('select value from last_seen')
		l_seen = cur.fetchone()[0]
		print l_seen
	except mdb.Error, e:
		print 'Error %d: %s' % (e.args[0], e.args[1])
		sys.exit(1)	

def downloader():
	global git_limit
	print 'Running in downloader mode'
	try:
		con = mdb.connect(db_ip, db_user, db_pass, db_name)
		cur = con.cursor()

		while git_limit > 5:
			cur.execute('select value from last_seen')
			l_seen = cur.fetchone()[0]
			print l_seen
			repos, git_limit = get_repos(git_user, git_pass, l_seen)
			jsonrepos = json.loads(repos)

			q = Queue.Queue()
			threads = []

			for repo in jsonrepos:
				tmp_itm = {}
				tmp_itm['clone_url'] = 'git://github.com/%s.git' % (repo['full_name'])
				tmp_itm['path'] = repo['full_name']
				print 'adding %s' % repo['full_name']
				q.put(tmp_itm)
				
			while not q.empty():
				if 10 >= threading.activeCount():
					q_itm = q.get()
					try:
						t = threading.Thread(target=dl_worker,args=(q_itm,))
						t.daemon = True
						t.start()
					finally:
						q.task_done()
							
			while threading.activeCount() > 1:
				time.sleep(0.1)
					
			for thread in threads:
				thread.join()
					
			q.join()
				
			l_seen = jsonrepos[-1]['id']
			print l_seen
			cur.execute('UPDATE last_seen SET value = "%s"' % (l_seen))
			con.commit()
			
			print 'You have 15 secs stop quit this script...'
			time.sleep(15)
			print 'Moving right along...'

	except mdb.Error, e:
		print 'Error %d: %s' % (e.args[0], e.args[1])
		sys.exit(1)
	finally:
		if con:
			con.close()

def grepper():
	print 'Running in grepper mode'

def processor():

	hd_val = {'USB_HDD2': 'I:\\', 'USB_HDD3': 'J:\\', 'USB_HDD1' : 'L:\\', 'USB_HDD4' : 'M:\\', 'USB_HDD5' : 'N:\\'}

	try:
		con = mdb.connect(db_ip, db_user, db_pass, db_name)
		cur = con.cursor()
		while True:
			cur = con.cursor()
			cur.execute('SELECT username,name,id,harddrive FROM projects WHERE processed = 0 and harddrive != "nhd" LIMIT 1')
			
			res = cur.fetchone()
			
			if len(res) == 0:
				print 'nothing to analyize'
			else:
				#all my stuff here
				cur.execute('UPDATE projects SET processed = 1 WHERE id = "%s"' % (res[2]))
				
				my_path = os.path.join(hd_val[res[3]],res[0], res[1])
				
				if os.path.exists(my_path):
					#print my_path
					for r,d,f in os.walk(my_path):
						for file in f:
							#print '%s' % file
							cur.execute("INSERT INTO files (name) VALUES ('%s') ON DUPLICATE KEY UPDATE count = count + 1" % (file.replace("'", '')))
					
						for dir in d:
							#print '%s' % dir
							cur.execute("INSERT INTO dirs (name) VALUES ('%s') ON DUPLICATE KEY UPDATE count = count + 1" % (dir.replace("'", "")))
					
					cur.execute('UPDATE projects SET processed = 2 WHERE id = "%s"' % (res[2]))
					con.commit()
					if cur:
						cur.close()
					print '%s%s\%s' %  (hd_val[res[3]], res[0], res[1])
					time.sleep(0.5)

				
	except mdb.Error, e:
		print 'Error %d: %s' % (e.args[0], e.args[1])
		sys.exit(1)
	finally:
		if con:
			con.close()

def get_repos(username, password, last_seen):
	url = 'https://api.github.com/repositories?since=%s' % (last_seen)
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
	b64s = base64.encodestring('%s:%s' % (username, password))
	req.add_header('Authorization', 'Basic %s' % (b64s))

	page = urllib2.urlopen(req)
	page_content = page.read()
	page.close()

	return page_content, page.info()['X-RateLimit-Remaining']

def main():
	setup()

	if args.mode == 'downloader':
		downloader()
	elif args.mode == 'grepper':
		grepper()
	elif args.mode == 'test':
		test()
	else:
		processor()
		

if __name__ == '__main__':
	main()

