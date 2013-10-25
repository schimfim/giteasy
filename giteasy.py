# giteasy.py
# One-file git access for python

import requests
from base64 import b64decode, b64encode
import json
import glob
from string import join
import json

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.ERROR)

API = 'https://api.github.com'

# Utilities
def content(d):
	return b64decode(d['content'])

def pretty(r):
	print(json.dumps(r, indent=2, sort_keys=True))

# REST access

# github API

# Repo
class Repo(object):
	def __init__(self, repo, user, pwd,
	             auto_create=True):
		self.auth = (user, pwd)
		self.rurl = '{}/repos/{}/{}'.format(API, user,
		                                   	repo)
		self.username = user
		self.last_sha = None
		self.auto_create = auto_create
		self.commit_msg = 'Auto commit by giteasy'
		self.repo = repo
		self.res = None 
		self.status = 0
		if self.exists():
			logging.info('Connected to %s as %s',repo,user)
		else: 
			logging.error('Could not connect to repo:'+repo)
			raise IOError()
	
	def makeRurl(self, parms):
		s = self.rurl
		for p in parms:
			s += '/' + p
		logging.debug('url=%s', s)
		return s
	
	def get(self, parms=[]):
		'''
		Wrapper for requests.get
		Builds url from parms
		Stores result in self.res
		Returns json content
		'''
		url = self.makeRurl(parms)
		r = requests.get(url, auth=self.auth)
		self.res = r
		self.status = r.status_code
		return r.json
	
	def put(self, data, parms=[]):
		'''
		Wrapper for requests.put
		'''
		url = self.makeRurl(parms)
		d = json.dumps(data) # otherwise get form encoded
		r = requests.put(url, data=d, auth=self.auth)
		self.res = r
		self.status = r.status_code
		return r.json
	
	def exists(self):
		# GET /repos/:owner/:repo
		self.get()
		if self.status == 200:
			return True 
		else:
			return False
		
	def download(self, name):
		# GET /repos/:owner/:repo/contents/:path
		r = self.get(['contents', name])
		#r=self.g.repos[user][repo].contents[name].get()
		logging.debug(json.dumps(r, indent=2,
		                         sort_keys=True))
		if self.status != 200:
			raise IOError('File not found: ' + name)
		logging.info('File loaded: ' + name)
		self.last_sha = r['sha']
		return content(r)
		
	def upload(self, name, content):
		# PUT /repos/:owner/:repo/contents/:path
		# There needs to be a default branch
		# in the repo before you can do this
		# (should be there if you did
		# auto_init=true on creation)
		
		# prepare message body
		b64 = b64encode(content)
		d = {'path':name,
		     'message':self.commit_msg,
		     'content':b64}
		     
		# Check if file exists and get sha
		try:
			self.download(name)
			sha = self.last_sha
			d['sha'] = sha
			self.last_sha = None
		except IOError:
			logging.warning('File not found: ' + name)
			if not self.auto_create:
				return
		
		# Create or update (needs sha)
		#r=self.g.repos[user]
		#[repo].contents[name].put(body=d)
		r = self.put(d, ['contents', name])
		if self.status not in (200, 201):
			logging.error('Could not upload file. Status: %i', self.status)
			raise IOError()
		logging.info('Uploaded file: ' + name)
	
	#
	def download_files(self, files):
		for name in files:
			try:
				txt = self.download(name)
				with open(name, 'w') as f:
					f.write(txt)
			except IOError:
				logging.warning('File not found: ' + name)
	
	def upload_files(self, files):
		for name in files:
			try:
				with open(name, 'r') as f:
					txt = f.read()
				self.upload(name, txt)
			except IOError:
				logging.error('Could not upload file: ' + name)
				raise
				
	# Class methods
	def repos(self):
		r = self.g.user.repos.get()
		for repo in r[1]:
			print repo['name']

	def create_repo(self, aname):
		r = self.g.user.repos.post(
			body={'name': aname, 'auto_init': True})
		return r

################
# CLI
import cmd

class RepoCLI(cmd.Cmd):
	def __init__(self, repo, user, pwd, files):
		cmd.Cmd.__init__(self)
		self.repo = Repo(repo, user, pwd)
		self.files = files
		self.cmdloop()
	
	def do_f(self, parms):
		# Show list of files
		print self.files
	def help_f(self, parms):
		print 'Show list of files'
	
	def do_d(self, parms):
		# Download files
		self.repo.download_files(self.files)

	def do_u(self, parms):
		# Upload files
		self.repo.upload_files(self.files)

	def do_o(self, parms):
		# Upload one file
		f = [parms]
		self.repo.upload_files(f)


if __name__ == '__main__':
	import os.path
	import os
	import editor
	import glob
	import sys
	import json
	filepath = editor.get_path()
	path = os.path.dirname(filepath)

	print 'path:', path
	os.chdir(path)
	print glob.glob('*.py')
	
	#sys.path.append(path)
	#import auth
	try:
		with open('gitauth.py') as f:
			auth = json.load(f)
	except IOError:
		auth = {}
		print 'No setup found. Please enter:'
		auth['repo'] = raw_input(' repository: ')
		auth['user'] = raw_input(' user: ')
		auth['pwd'] = raw_input(' password: ')
		auth['ignore'] = []
		with open('gitauth.py','w') as f:
			json.dump(auth, f)
		
	py = set(glob.glob('*.py'))
	ignore = set(auth['ignore'] + ['gitauth.py'])
	files = py - ignore
	RepoCLI(auth['repo'], auth['user'],
	        auth['pwd'] , files)
	
