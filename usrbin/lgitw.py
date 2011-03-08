#!/usr/bin/env python
# Edit the version in ~/Documents/unix/python/pgms/DU/usrbin
# lgitw.py
#
__author__ = "Robert E. Hoot (rehoot@yahoo.com)"
__version__ = "0.01"
__date__ = "$Date: 2010/01/07 $"
__copyright__ = "Copyright 2010, Robert E. Hoot"
__license__ = "GNU General Public License Version 3, 29 June 2007"
#####################################################################
# This file is part of the lgit system.
# lgit is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3
# of the License.
#
# lgit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public
# License along with lgit. If not, see
# <http://www.gnu.org/licenses/>.
#####################################################################
# Purpose:
# 1) This version will operate on a single git working tree
#    as determined by the current working directory and
#    as indexed in the lgit file list (~/.lgitconf).
# 1b) The format of an entry in the ~/.lgitconf file is a nickname
#     and then "-files" such as this example with nickname "usrbin"
#        [usrbin-files]
#        usrbin = /usr/bin
# 2) This program will be used for operations on a single directory,
#    such as checking out a single file or old commit.
#
# note on upgrade to python 3.1 from 2.5
#   For some reason os.getenv("PWD") worked for regular user ID
#   but not for root.  
#   I switched to os.getcwd()`
import sys
if (sys.version < "3"):
	print("Error. This script requires python 3.0 or higher")
	sys.exit(-1)

import os
import shutil
import tempfile
import re
from lgitlib import *

cmdparsed = [""]

def main():
	# globals from lgitlib:
	global opts
	global safecmds
	global dontneedroot

	# Initialize using lgitlib functions:
	load_options()

	if len(sys.argv) != 2:
		usage()
		return(-1)
		# yea, I put a return statement in the middle of the function.
		# So what!

	else:
		gcmd = sys.argv[1]
		cmdparsed = re.split("[ ]",gcmd)


		# find the current working directory and resolve any links if
		# the directory was accessed through the link.
		cwd = fixpath(os.getcwd())
		# scanwrklist() will return a list that contains
		# two elements: (a) the full path to the git repository that
		# is associated with the current working directory,
		# and (b) the "code" under which that directory is
		# coded in the ~/.lgitconf file -- it can also be used 
		# to find options that are unique to this repository.
		L = scanwrklist(cwd)
		newgitdir = L[0]
		# gitpath gives the option name that is associated with this
		# path.  I might need that later for push and pull commands.
		sectname = L[1]
	
		if(opts[sectname]["requireroot"]):
			if (os.getenv("USER") != "root") & (cmdparsed[0].lower()
					not in dontneedroot):
				print("Error. Run this particular git command using "
				+ "the root user ID.")
				return(-1)
		if (newgitdir != ""):
			print("Processing the current directory using repository: " 
						+ newgitdir) 

			if(cmdparsed[0].lower() in (["gitk", "git-gui", 
					"tig", "qgit"])):
				# Note that ci-tool and gui use the normal lgit 
				# command interface
				# but might not work anyway.
				execcmd = cmdparsed[0] + " --work-tree=" + cwd \
						+ " --git-dir=" + newgitdir 
				print("WARNING: the various graphical interfaces "
						+ "might not work if they do not support "
						+ "the use of options like --work-tree and "
						+ "--git-dir.")
			else:
				execcmd = "git --no-pager --work-tree=" + cwd \
						+ " --git-dir=" + newgitdir + " " + gcmd
			
			rc = os.system(execcmd)
			if (rc != 0 and rc != 256):
				print("Error. git returned an error")
				print("The error code is %d" % rc)

			# Consider changing the file permissions on either all or 
			# selected directories (e.g., avoid letting the checkout 
			# command make your git repository owned by root)
			if(opts[sectname]["unlockgitdir"]):
				if(os.getenv("USER") == "root"):
					print("Unlocking git dir") #reminder to the user
					change_git_dir_owner(newgitdir)

		else:
			print("Error. The current directory (" + newgitdir 
					+ ") is not listed in " 
					+ str(opts[sectname]["git_rep_root"]) 
					+ " as a git working directory.")

def usage():
	print("lgitw.py usage:")
	print("First change your current directory to a LaTeX working "
		+ "directory (where the real LaTeX files are)")
	print("or other file registered in ~/.lgitconf.")
	print("From that working directory, run the lgitw.py command "
			+ "and Enclose a git command in double quotes like this:")
	print("  lgitw.py \"tag V1.2\"")
	print("Also note that some command must be run with the root "
				+ "user ID (commit, gc, checkout, reset...).")


def scanwrklist(cwd):
	"""If the specified directory is being tracked as specifed in
    ~/.lgit.conf, return a list object that contains two items:
	(1) the full path to the git directory that is associated with 
	the current working directory, and (2) the name of the options 
	section. If no match is found, this will return a list object
	with two empty strings.

	Pass a string that represents the well-formated current, working
	directory (cwd).
  """
	global flist

	unwanted_options = []
	cleancwd = fixpath(cwd)
	gitdirL = ["", ""]
	for L in flist.items():
		# flist is a dictionary of codes and paths.
		# print(repr(q) + repr(r) )
		f = fixpath(L[1][0]) #file name
		# The sectname is two things in one: the section name
		# in the options file and the subdirectory name
		# in the git repository.
		sectname = L[1][1]
		if(f == cleancwd):
			dprint(5, sectname, "in scanlist, " + f + " sectname: " + sectname)
			gitdirL[0] = ensure_trailing_slash(
				fixpath(opts[sectname]["git_rep_root"])) + sectname  
			# load the section
			gitdirL[1] = sectname
	return(gitdirL)

if __name__ == '__main__':
	main()

