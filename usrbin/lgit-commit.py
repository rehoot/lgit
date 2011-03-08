#!/usr/bin/env python
# Edit the version in ~/Documents/unix/python/pgms/DU/usrbin
# lgit-commit.py
#
__author__ = "Robert E. Hoot (rehoot@yahoo.com)"
__version__ = "0.01"
__date__ = "$Date: 2010/01/07 $"
__copyright__ = "Copyright 2010, Robert E. Hoot"
__license__ = "GNU General Public License Version 3, 29 June 2007"
#####################################################################
# This file is part of the lgit system.
#
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
#
# For conversion to python 3.1 from 2.5:
#   1) I had to change how .translate works, and I used replace() 
#      instead of translate for the cmdmsg.
#
import sys
if (sys.version < "3"):
  print("Error. This script requires python 3.0 or higher")
  sys.exit(-1)

import os
import shutil
import tempfile
import re
from lgitlib import *

def main():
	global opts
	global flist

	if os.getenv("USER") != "root":
		print("Error.  You must run this command under the root "
		+ "user ID.")
		return(-1)

	if len(sys.argv) != 3:
		usage()
		return(-1)
	else:
		load_options()

		# build a translation table
		stbl = ""
		trtbl = ""
		for j in range(0, 256):
			stbl = stbl + "%c" % j

		# Verify the format of the commit tag using the option set
		# in the .lgitconf file.  NOTE that re.match() will return
		# none if there is no match or will return a 'match' object
		# if they do match.
		tagname = sys.argv[1].upper()
		if(re.match(opts["lgit"]["tag_regexp"],tagname) == None):
			print("Error. The tag: " + tagname 
				+ ", does not match the regular"
				+ "expression format that is specified in the "
				+ CONF_FILE_NAME + " file: "
				+ opts["lgit"]["tag_regexp"] + "\n(case sensitive)")

			return(-1)
		#
		# Replace some potentially confusing characters from the 
		# commit message.
		cmsg = sys.argv[2].replace('"',":").replace("'",":")

		print("TEST-commit, before processfiles")
		process_files(cmsg, tagname)

def usage():
	print("lgit-commit.py usage:")
	print( "The first paramater is a tag that starts with a "
		+ " capital letter V and does not contain any embedded spaces")
	print("The second paramater is a commit message in double "
		+ "quotes (avoid using embedded quotes inside it)")

def process_files(commitmsg, tag):
	"""Take a commit message and commit tag value, then add the working and git 
	directories to the command and issue a commit command.
	"""
	global opts
	global flist
	
	for f in flist.keys():
		print("testing wrk dir loop in process_files" + f)
		# The value of f is the name of the subdirectory, such as 
		# "texmf-dist", which is under the git root repository root
		# directory (~/gits). That key
		# also points to the full working directory path inside
		# the flist dictionary.
		wrkdir = fixpath(flist[f][0])
		gitdir = fixpath(opts["lgit"]["git_rep_root"] + f)

		print("=============================================")
		print("Processing " + wrkdir + ":" )
		print("The git dir is " + gitdir)
		#
		#
		os.chdir(wrkdir) #change directory, which is important for 
		#                 some git commands
		#
		cmd1 = "git --git-dir=" + gitdir \
					+ " --work-tree=" + wrkdir + " commit " \
					+ "--allow-empty -a -m \"" + commitmsg + "\""
		rc = os.system(cmd1)
		if rc == 0:
			print("The commit returned a good code, so I will tag "
			+ "the commit")
			cmd2 =  "git --git-dir=" + gitdir + " --work-tree=" \
				+ wrkdir + " tag " + tag
			rc2 = os.system(cmd2)
		else:
			print("Error.  Commit returned an error")
	#END LOOP
	#	
	if(opts["lgit"]["unlockgitdir"]):
		if(os.getenv("USER") == "root"):
			# Post a reminder to the user about unlocking the gitdir.
			print("Unlocking the git repository: " + gitdir)
			change_git_dir_owner(gitdir)
	#		
if __name__ == '__main__':
	main()

