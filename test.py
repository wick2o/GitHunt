#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys

def worker(itm):
	pass
	
def get_folders(main_path):
	for root,dirs,files in os.walk('.'):
		for dir in dirs:
			print os.path.join(root,dir)
			

def main():
	get_folders()
	

	
if __name__ == "__main__":
	main()