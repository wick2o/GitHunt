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
import gc
import datetime

halt = False


try:
	import argparse
except:
	print 'Missing needed module: easy_install argparse'
	halt = True

try:
	import psutil
except:
	print 'Missing needed module: easy_install psutil'
	halt = True
try:
	import simplejson as json
except:
	print 'Missing needed module: easy_install simplejson'
	halt = True
	
try:
	from git import *
except:
	print 'Missing needed module: easy_install gitpython'
	halt = True
	
if halt == True:
	sys.exit()

socket.setdefaulttimeout(120)

rate_limit_left = 5000

def get_repos(last_seen, user, u_pass):
	global rate_limit_left
	
	url = 'https://api.github.com/repositories?since=%s' % (last_seen)
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
	b64s = base64.encodestring('%s:%s' % (user, u_pass))
	req.add_header('Authorization', 'Basic %s' % b64s)
	
	page = urllib2.urlopen(req)
	page_content = page.read()
	page.close()
	
	rate_limit_left = page.info()['X-RateLimit-Remaining']
	
	return page_content 


def setup():
	parser = argparse.ArgumentParser()
	parser.add_argument('-u', '--username', action='store', dest='username', required=True, help='github username')
	parser.add_argument('-p', '--password', action='store', dest='password', required=True, help='github password')
	parser.add_argument('-o', '--output', action='store', dest='output', required=True, help='base path for output')
	
	global args
	args = parser.parse_args()
	
def worker(itm):

	try:
		o_path = '%s/%s' % (args.output, itm['path'])
		res = git.Git().clone(itm['clone_url'], o_path)
		tmp_item = {}
		tmp_item['username'] = itm['path'].split('/')[0].strip()
		tmp_item['name'] = itm['path'].split('/')[1].strip()
		need_processed.append(tmp_item)
		del tmp_item
		print '%s\n' % res
except:
		pass
		
def main():
	setup()

	last_seen = 913620
	
	while rate_limit_left > 5:
		repos = get_repos(last_seen, args.username,args.password)
	
		jsonrepos = json.loads(repos)

		q = Queue.Queue()
		threads = []
		
		global need_processed
		need_processed = []

		for repo in jsonrepos:
			#print repo['full_name']
			#print repo['owner']['login']
			clone_url = 'git://github.com/%s.git' % repo['full_name']
			#subprocess.call(['git', 'clone', clone_url, repo['full_name'] ])
			#*****  worker(clone_url, repo['full_name'])
			tmp_item = {}
			tmp_item['clone_url'] = clone_url
			tmp_item['path'] = repo['full_name']
			q.put(tmp_item)
			del tmp_item
			
		while not q.empty():
			if 10 >= threading.activeCount():
				q_itm = q.get()
				try:
					t = threading.Thread(target=worker,args=(q_itm,))
					t.daemon = True
					threads.append(t)
					t.start()
				finally:
					q.task_done()
					
		while threading.activeCount() > 1:
			time.sleep(0.1)
			
		for thread in threads:
			thread.join()
			
		q.join()
				
			
		last_seen = jsonrepos[-1]['id']
		
		f=open('logfile.txt','w')
		f.write('Current rate_limit_left: %s  Current last_seen: %s...' % (rate_limit_left, last_seen))
		f.close()
		
		f_name = '%s.log' % (datetime.datetime.now().strftime("%Y-%m-%d"))
		f=open(f_name, 'a')
		for itm in need_processed:
			f.write('INSERT INTO projects (username, name) VALUES ("%s", "%s");\n' % (itm['username'], itm['name']))
		f.close()
		
		print 'updated %s\n' % (f_name)
		
		del jsonrepos
		del q
		del threads
		
		gc.collect()
		#time.sleep(700)
		
		print 'You have 15 secs to quit this script...'
		time.sleep(15)
		print 'Moving right along...'
				
				
				
	
	print 'I hit my rate limit last_seen: %s' % last_seen
	sys.exit()	
	
if __name__ == "__main__":
	main()