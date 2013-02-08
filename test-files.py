#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import Queue
import signal
import time
import gc

from threading import Thread, activeCount, Lock, current_thread
from datetime import datetime

halt = False

try:
	import argparse
except:
	print 'Missing module: easy_install argparse'
	halt = True
	
if halt == True:
	sys.exit()

sigint = False
queue = Queue.Queue()

def progressbar(progress, total):
	global args
	progress_percentage = int(100 / (float(total) / float(progress)))
	sys.stdout.write("%s%% complete\r" % (progress_percentage))

def run_process_files(itm):
	global args
	
	itm_dir =  os.path.join(args.folder, itm)
	
	for r,d,f in os.walk(itm_dir):
		f_out.write('\n'.join(f))
		
	del itm_dir
		
	gc.collect()
		
def run_process_dirs(itm):
	global args
	
	itm_dir = os.path.join(args.folder, itm)
	
	for r,d,f in os.walk(itm_dir):
		f_out.write('\n'.join(d))
		
	del itm_dir
		
	gc.collect()
	
def process_handler(task_data):
	global args
	process = 0
	
	if args.threads > 1:
		threads = []
		for itm in task_data:
			queue.put(itm)
		progress_lock = Lock()
		
		while not queue.empty() and not sigint:
			if args.threads >= activeCount() and not sigint:
				q_itm = queue.get()
				try:
					if args.project == 'files':
						t = Thread(target=run_process_files, args=(q_itm,))
					elif args.project == 'dirs':
						t = Thread(target=run_process_dirs, args=(q_itm,))
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
	global args
	global sigint
	global s_time
	
	sigint = True
	
	print 'Ctrl+C detected... exiting...\n'
	
	print 'The script has fun for:'
	print datetime.now() - s_time

	sys.exit(1)
	
def setup():
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', '--folder', action='store', dest='folder', required=True, help='Root Folder')
	parser.add_argument('-o', '--output', action='store', dest='output', required=True, help='Where to save output')
	parser.add_argument('-t', '--threads', action='store', dest='threads', default=0, type=int, help='number of threads')
	parser.add_argument('-p', '--project', action='store', dest='project', choices=['files','dirs'], default='files', help='List to create')
	
	global args
	args = parser.parse_args()

def main():
	setup()
	
	global s_time
	s_time = datetime.now()
	
	if os.path.isdir(args.folder) == True:
		usernames = os.listdir(args.folder)
	else:
		print '-f was not a folder...'
		sys.exit()
	
	global f_out
	f_out = open(args.output, 'w')
	
	process_handler(usernames)
	
	f_out.close()
	
	print 'The script has run for:'
	print datetime.now() - s_time
		
if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler)
	main()