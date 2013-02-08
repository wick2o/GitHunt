#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

usernames = os.listdir('.')

for user in usernames:
	try:
		for proj in os.listdir(os.path.join('.',user)):
			print 'INSERT INTO projects (username, name) VALUES ("%s", "%s");' % (user,proj)
	except:
		pass