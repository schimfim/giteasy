# giteasy.py
# Simplified git access for python
# TODO:
# - use Repo class
# - cleanup code

from agithub import Github
from base64 import b64decode, b64encode
import json

import logging
logging.basicConfig(level=logging.INFO)

# Utilities
def content(d):
	return b64decode(d['content'])

def pretty(r):
	print(json.dumps(r, indent=2, sort_keys=True))

# API
# Abstraction of the low level github api
# introducing functional interfaces and
# exceptions
class Giteasy(object):
	def __init__(self, user, pwd):
		self.g = Github(user, pwd)
		self.username = user

	def repos(self):
		r = self.g.user.repos.get()
		for repo in r[1]:
			print repo['name']

	def create_repo(self, aname):
		r = self.g.user.repos.post(
			body={'name': aname, 'auto_init': True})
		return r

# Repo
class Repo(object):
	def __init__(self, repo, user, pwd, auto_create=True):
		self.g = Github(user, pwd)
		self.username = user
		self.last_sha = None
		self.auto_create = auto_create
		self.commit_msg = 'Auto commit by giteasy'
		self.repo = repo
		if self.exists():
			logging.info('Connected to repo: ' + repo)
		else: 
			logging.info('Could not connect to repo:' + repo)
	
	def exists(self):
		# GET /repos/:owner/:repo
		status, r = self.g.repos[self.username][self.repo].get()
		if status == 200:
			return True 
		else:
			return False
		
	def download(self, name):
		# GET /repos/:owner/:repo/contents/:path
		user = self.username
		repo = self.repo
		status, r = self.g.repos[user][repo].contents[name].get()
		logging.debug(json.dumps(r, indent=2, sort_keys=True))
		if status != 200:
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
		user = self.username
		repo = self.repo
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
			logging.info('File not found: ' + name)
			if not self.auto_create:
				return
		
		# Create or update (needs sha)
		status, r = self.g.repos[user][repo].contents[name].put(body=d)
		if status not in (200, 201):
			logging.error('Could not upload file. Status: {}'.format(status))
			pretty(r)
			raise IOError('Could not upload file')
		logging.info('Uploaded file: ' + name)
	
	#
	def download_files(self, files):
		for name in files:
			try:
				txt = self.download(name)
				with open(name, 'w') as f:
					f.write(txt)
			except IOError:
				logging.info('File not found: ' + name)
	
	def upload_files(self, files):
		for name in files:
			try:
				with open(name, 'r') as f:
					txt = f.read()
				self.upload(name, txt)
			except IOError:
				logging.error('Could not upload file: ' + name)
				raise

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

