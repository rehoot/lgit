# run this from the UNIX command line as:
#   cd thedirectory_where_setup.py_is
#   python setup.py sdist
from distutils.core import setup 
import shutil
import os
import stat
import glob
import sys


def fixpath(thepath):
	"""Expand the ~/ shortcut if present, resolve any links in the path,
	and remove any double slashes from the path
	"""
	return (os.path.normpath(os.path.realpath(os.path.expanduser(
					os.path.expandvars(thepath)))))

setup(name='lgitlib',
  version='1.0', 
	description='lgitlib - parallel version control for multiple project directories or project directories with foreign git repositories.',
	author='Robert E. Hoot',
	author_email='rehoot@yahoo.com',
	py_modules=['lgitlib'],
)

# now check the path and copy the files in usrbin
# to an executable directory.

if(sys.argv[1].lower() == "install"):
	print("Copying Python scripts to " + os.path.join(
		os.path.sep, "usr", "bin"))
	copy_L = glob.glob(fixpath(os.path.join(".", "usrbin", "*")))
	for f in copy_L:
		shutil.copy(f, fixpath(os.path.join(os.path.sep, "usr", "bin")))
	L = glob.glob(os.path.join(os.path.sep, "usr", "bin", "lgit*.py"))
	for f in L:
		os.chmod(f, stat.S_IRGRP + stat.S_IROTH + stat.S_IRUSR 
			+ stat.S_IXGRP + stat.S_IXOTH + stat.S_IXUSR)
