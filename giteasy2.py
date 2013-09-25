import requests

API = 'https://api.github.com'

class Repo(object):
	def __init__(self, repo, user, pwd):
		self.auth = (user, pwd)
		self.repo = repo
		self.owner = user
		self.rurl = '{}/repos/{}/{}'.format(API, user,
		                                   	repo)
		                                   	
		                                   	
	def makeRurl(self, *parms):
		s = self.rurl
		for p in parms:
			s.append('/' + p)
		return s

	def getRepo(self):
		# GET /repos/:owner/:repo
		r = requests.get(rurl, auth=self.auth)
		print r.url
		print r.status_code
		print r.json
			
	def download(self, name):
		# GET /repos/:owner/:repo/contents/:path
		url = self.makeRurl('contents',name)
		***

r = Repo('testrepo', 'schimfim', 'Ninz2009')
r.getRepo()

