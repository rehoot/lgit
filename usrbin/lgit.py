#!/usr/bin/env python
# Edit the version in ~/Documents/unix/python/pgms/DU/usrbin
#
# lgit.py
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
#
# Purpose:
#  1) Perform version control for multiple directories in a parallel 
#     fashion.
#  2) Enforce the use of tags when committing (this script will tell 
#     the user to use the lgit-commit.py command).
#  3) Provide some basic error checking for existence of the working 
#     and git directories.
#  4) Require the user to run some commands from the root user ID 
#     (unless the option is disabled).
#  5) Allow all git commands to be applied across the set of tracked 
#     working directories.
#
# To Do:
# 1) create latex scripts to put the current commit info into each
#    document. 
#    The current commit can be found by running something like:
#	  tail -n 1 ~/Documents/.git/logs/HEAD|cut -f 2 -d ' '
#    and the current branch is in .git/HEAD
#
#
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

cmdparsed = [""]

def main():
	global cmdparsed
	# Some globals from lgitlib:
	global safecmds
	global dontneedroot

	# Initialize using lgitlib functions:
	load_options()
	#
	## VARIABLE ARG LIST JAN 12 2010
	new_argv = []
	for s in sys.argv:
		stmp = s
		spc = s.find(" ")
		eqsign = s.find("=")
		if(spc >0 or eqsign >=0):
			# I might need to add quotes somewhere because
			# sys.argv would strip quotes from a command-line
			# option like this: -a msg="my commit msg"
			if(spc > eqsign):
				# this looks like an equals sign as an option
				# followed by quotes with embedded spaces,
				# so I will put whater is after =
				# into quotes
				if(eqsign >= 0):
					stmp = s[0:eqsign + 1] + '"' + s[eqsign + 1:] + '"'
				else:
					stmp = '"' + s + '"'
		new_argv.append(stmp)

	if len(sys.argv) != 2:
		usage()
		return(-1)
		# yea, I put a return statement in the middle of the function.
		# So what!
	else:	
		gcmd = sys.argv[1]
		cmdparsed = re.split("[ ]", gcmd)
		#
		if(opts["lgit"]["requireroot"]):
			if (os.getenv("USER") != "root") & (cmdparsed[0].lower() 
					not in dontneedroot):
				print("Error. Run this particular git command using "
							+ "the root user ID.")
				return(-1)
		#
		if cmdparsed[0].lower() == "commit":
			print("Error. Use the lgit-commit.py command for commits.")
			return(-1)
		#
		if cmdparsed[0].lower() == "setup":
			# Perform a one-time setup of options.
			if(not bSetupRan):
				# Run setup only if the load_options command has not
				# already detected a missing config file and thereby
				# ran setup().
				yn = yn_input("Do you want to re-initialize options " 
							+ "for the lgit system? (y/n)")
				if(yn == "y"):
					setup()# This is in lgitlib.py
					print("check the options in " + CONF_FILE_NAME)
					# To Do: perhaps display all options for the user 
					# and the log file.
				else:
					print("Skipping setup and exiting.")
			return(0)
		#if cmdparsed[0].lower() in (["clone", "pull", "push"]):
		if cmdparsed[0].lower() in (["clone"]):
			print("ARE YOU CRAZY? Do not use lgit to clone.")
			return(-1)
		# Scan the list of directories in ~/.lgitfiles to see
		# if they look OK.
		if (validate_dirs(gcmd) != 0):
			print("Stopping execution before processing git commands.")
			return(-1)
		process_files(gcmd)
		#
		return(0)
		
def usage():
	print("lgit.py usage:")
	print("Enclose a git command in double quotes like this:")
	print("  lgit.py \"tag V1.2\"")
	#print("Also note that some commands must be run with the "
	#		+ "root user ID (commit, gc, checkout, reset, etc.).")

def process_files(gitcommand):
	"""Take a given git command and add the working and git 
	directories to the command.
	"""
	global flist
	for f in flist.keys():
		# The value of f is a text string that contains 
		# the nickname of the subdirectory in the git
		# repository, such as "texmf-dist", and inside flist, that key
		# also points to a 2-item array that contains 
		# the full working directory path and the options section
		# name (such as 'lgit').
		  #
		wrkdir = fixpath(flist[f][0])
		gitdir = fixpath(opts["lgit"]["git_rep_root"] + f)

		print("=============================================")
		print("Processing " + wrkdir + ":" )
		# To do: add a test for dir mode here
		print("The git dir is " + gitdir)
		# The "cd" command is needed to prevent unpacking files
		# into the wrong directory for commands like reset and checkout.
		####
		# TESTING TO ADD AN ADDITIONAL OPTION 
		# FOR PUSH, PULL, FETCH, MERGE
		# 
		pushpullrepository = ""
		pushpullrefspec = ""
		if(gitcommand.lower() == "push"):
			# The pushpull value will not be cleansed in any way
			pushpullrepository = pushrepositorylist[f][0]
			pushpullrefspec = pushrefspeclist[f][0]
		if(gitcommand.lower() == "pull"):
			# The pushpull value will not be cleansed in any way
			pushpullrepository = pullrepositorylist[f][0]
			pushpullrefspec = pullrefspeclist[f][0]
		####
		os.chdir(wrkdir) # Change directory, which is important for 
		#                # some git commands.
		cmd1 = "git --no-pager --git-dir=" \
				+ gitdir + " --work-tree=" + wrkdir + " " + gitcommand 
		
		skipdir = False
		if((pushpullrepository != "") or (pushpullrefspec != "")):
			cmd1 = cmd1 + " " + pushpullrepository + " " + pushpullrefspec
			print("TEST pp " + cmd1)
		if(gitcommand.lower() == "pull"):
			if(opts["lgit"]["promptonpushpull"]):
				yn =  input(gitcommand \
					+ " using repository: " + pushpullrepository  \
					+ " and refspec (branches): "  + pushpullrefspec \
					+ "? (y/n/q/o=override) ").lower()
				if(yn == "n"):
					print("Skipping this directory.")
					skipdir = True
				elif(yn == "q"):
					print("Quitting now.")
					sys.exit(-1)
				elif(yn == "y"):
					skipdir = False
				elif(yn == "o"):
						pushpullrepository = input("enter the new repository: ").lower()
						pushpullrefspec = input("enter the new refspec (such as " \
												   + "master:master): ").lower()
						print("You entered repository: " + pushpullrepository \
								  + " and a refspec of: " + pushpullrefspec)
						yn = yn_input("Continue? (y/n): ")
						if(yn == "n"):
							sys.exit(-1)
				else:
					print("You did not enter y, n, q, or o, so I quit.")
					sys.exit(-1)
						
		if(not skipdir):
			rc = os.system(cmd1)
			if( rc != 0 and rc != 256):
				# This section could use some enhanced error processing.
				# Perhaps use the errno module or os.strerror().
				# The git status command returns an error when the 
				# status is clean.
				print("Error. git returned an error")
				print("The error code is %d" % rc)
	###### END LOOP
	
	# Change the file permissions on the git directory if specified
	# in the options. This can reduce some file access problems when
	# some git commands are run under root and others are not.
	# --This should ideally run before any error exit.
	if(opts["lgit"]["unlockgitdir"]):
		if(os.getenv("USER") == "root"):
			# Post a reminder to the user about unlocking the gitdir.
			print("Unlocking the git repository: " + gitdir)
			change_git_dir_owner(gitdir)

def validate_dirs(gcmd):
	"""Scan the list of work and git directories 
	and confirm that this program has adequate access (read or 
	write depending on the git command). This should run before
	processing any git commands so that the user can be warned
	if one or more of the directories is bad (inaccessible).
	"""
	global flist
	global cmdparsed
	global dontneedroot

	baddirs = []#list will hold bad directories
	for f in flist.keys():
		# The value of f is the name of the subdirectory in the git
		# repository, such as "texmf-dist", and inside flist, that key
		# also points to the full working directory path.
	  #
		dprint(3, "lgit", "Validating git repository: " 
				+ repr(flist[f]))
		wrkdir = fixpath(flist[f][0])
		gitdir = fixpath(opts["lgit"]["git_rep_root"] + f)
		if wrkdir[0] not in (["/", ":", os.sep]):
			baddirs.append([wrkdir, "Path should be specified " 
			+ "relative to root directory, starting with " + os.sep])
		# Check for existence of work dir, and if required,
		# Check for write access.
		if os.access(wrkdir, os.F_OK):
			# The work directory exists.  Do more tests if root is 
			# required per the options.
			if(opts["lgit"]["requireroot"]):
				if cmdparsed[0].lower() not in(dontneedroot):
					# This command requires the root ID and perhaps 
					# needs write access to the working directory.
					if not os.access(wrkdir, os.W_OK):
						baddirs.append([wrkdir,
						"No write access to the work " 
						+ "directory: " + wrkdir + ". You might "
						+ "need to run this command using the root user"
						+ " ID (via the sudo command)"])
		else:
			baddirs.append([wrkdir,"does not exist"])

		# check for existence of git dir, and if required,
		# check for write access.
		if os.access(gitdir, os.F_OK):
			if(opts["lgit"]["requireroot"]):
				if cmdparsed[0].lower() not in(dontneedroot):
					# This command might need to write to the git 
					# repository, so check for write access.
					if not os.access(gitdir, os.W_OK):
						baddirs.append([gitdir,
						"No write access to the git "
						+ "repository: " + gitdir + ". You might need "
						+ "to run this command using the root user ID "
						+ "(via the sudo command)"])
		else:
			baddirs.append([gitdir,"does not exist"])
	if len(baddirs) > 0:
		# Print error messages and return an error code
		for j in range(len(baddirs)):
			print("Error. " + baddirs[j][0] + " - " + baddirs[j][1])
		return(-1)
	#
	# The list of directories has been scanned, and no problems
	# were found, so return a normal code.
	return(0)

if __name__ == '__main__':
	main()

