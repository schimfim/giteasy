from giteasy import RepoCLI
import glob

files = set(glob.glob('*.py')) - set(['sync.py'])
RepoCLI('giteasy', 'schimfim', 'Ninz2009', files)
