#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import urllib
import urllib2
import re

import signal
import Queue
from threading import Thread, activeCount, Lock, current_thread

sigint = False
queue = Queue.Queue()
results = []

halt = False

try:
	import argparse
except:
	print 'Missing needed module: easy_install argparse'
	halt = True
	
try:
	import yaml
except:
	print 'Missing needed module: easy_install yaml'
	halt = True
	
try:
	import sqlite3
except:
	print 'Missing needed module: easy_install sqlite3'
	halt = True
	
if halt == True:
	sys.exit()
	
def progressbar(progress, total):
	progress_percentage = int(100 / (float(total) / float(progress)))
	sys.stdout.write("%s%% complete\r" % (progress_percentage))
	
def run_process(itm):
	url = itm
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
	
	page = urllib2.urlopen(req)
	page_content = page.read()
	
	if page_content != None:
		db = re.compile('<h2 class="title">\s*?<a.*?>(.*)</a>\s*?<span class="aka">(.*)</span>\s*?<span class="email">(.*)</span>\s*?</h2>', re.I | re.M)
		my_res = db.findall(page_content)
		for res in my_res:
			if not res[0].strip() in results:
				results.append(res[0].strip())
				print 'found %s\n' % (res[0].strip())
			
	page.close()

	
def generate_task_data():
	my_task_data = []
	
	search_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
	
	f=open('../conf/languages.yml', 'r')
	languages = yaml.safe_load(f)
	f.close()
	
	for lang in languages['languages']:
		for letter in search_chars:
			for idx in range(1,99):
				my_task_data.append('https://github.com/search?q=%s&p=%s&ref=searchbar&type=Users&l=%s' % (letter,idx,lang.replace(' ','+')))

	return my_task_data
	
def process_handler(task_data):
	global args
	progress = 0
	
	if args.threads > 1:
		threads = []
		for itm in task_data:
			queue.put(itm)
		progress_lock = Lock()
		
		while not queue.empty() and not sigint:
			if args.threads >= activeCount() and not sigint:
				q_itm = queue.get()
				try:
					t = Thread(target=run_process, args=(q_itm,))
					t.daemon = True
					threads.append(t)
					t.start()
				finally:
					progress = len(task_data) - queue.qsize()
					progress_lock.acquire()
					try:
						progressbar(progress, len(task_data))
					finally:
						progress_lock.release()
					queue.task_done()
					
		while activeCount() > 1:
			time.sleep(0.1)
		for thread in threads:
			thread.join()
			
		queue.join()
	else:
		for itm in task_data:
			run_process(itm)
			progress += 1
			progressbar(progress, len(task_data))
			if sigint == True:
				signal_handler('','')
	return
		
		
def signal_handler(signal, frame):
	global sigint
	
	sigint = True
	print 'Ctrl+C detected... exiting...\n'
	sys.exit(1)
	
def database_check(db_name):
	if os.path.exists(db_name):
		print 'Skipping database generation, %s already exists...' % (db_name)
	else:
		db = sqlite3.connect(db_name)
		db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY,name varchar(255),found_on varchar(100),last_checked varchar(100))')
		db.commit()
		db.close()

def setup():
	parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--threads', action='store', dest='threads', default=0, type=int, required=True, help='Enable Threading. Specifiy max # of threads')
	
	global args
	args = parser.parse_args()

def main():

	setup()
	
	database_check('..\data.db')
	print 'generateing tasks...'
	task_data = generate_task_data()
	
	print 'running processes'
	process_handler(task_data)
	
	db = sqlite3.connect('..\data.db')
	
	for name in results:
		c = db.cursor()
		c.execute("INSERT INTO users ('name','found_on') VALUES ('%s','%s')" % (name, datetime.datetime.now()))
		
	db.commit()
	
	if c:
		c.close()
	if db:
		db.close()
	
	
	#run_process('https://github.com/search?q=9&p=1&ref=searchbar&type=Users&l=JavaScript')


if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler)
	main()