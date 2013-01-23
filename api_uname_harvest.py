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

halt = False

try:
	import argparse
except:
	print 'Missing needed module: easy_install argparse'
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

socket.setdefaulttimeout(45)

rate_limit_left = 5000

def get_repos(last_seen, user, u_pass):
	global rate_limit_left
	
	url = 'https://api.github.com/repositories?since=%s' % (last_seen)
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
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
	
	global args
	args = parser.parse_args()
	
def main():
	setup()

	last_seen = 0
	
	while rate_limit_left > 5:
		repos = get_repos(last_seen, args.username,args.password)
	
		jsonrepos = json.loads(repos)
	
		for repo in jsonrepos:
			#print repo['full_name']
			#print repo['owner']['login']
			clone_url = 'git://github.com/%s.git' % repo['full_name']
			subprocess.call(['git', 'clone', clone_url, repo['full_name'] ])
			
			
			sys.exit()
			
		last_seen = jsonrepos[-1]['id']
	
	
	print 'I hit my rate limit last_seen: %s' % last_seen
	sys.exit()	
		
	
	
	

	
if __name__ == "__main__":
	main()