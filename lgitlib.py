# lgtilib.py, edit the version in ~/Documents/unix/python/pgms/DU/lgitlib.py
# and then install as a python library.
#
# to do:
#  fix the export_default_options routine or add a new
#  one that can append default options for a new tracking group.
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
import configparser
import os
import subprocess
import re 
import shutil 
import datetime
import sys
#
# The conf_file_portlist will be converted
# into a path using fixpath() and portpath()
# and then loaded into CONF_FILE_NAME as a string
# in hopes of making the path specification more portable
# across operationg systems.
conf_file_portlist = ["~", ".lgitconf"]
CONF_FILE_NAME = ""
#
bSetupRan = False
#
# Options from the config file will be loaded into global 
# dictionaries. The opts dictionary will contain other
# dictionaries keyed by section name (section of the config
# file exclusive of any section name that contains a hyphen).
#    >>> lgitlib.opts
#      {'lgit': {'debuglvl': 0, 'requireroot': True, 'git_rep_root': '~/gits/', 'unlockgitdir': True, 
#           'debug_prompt': False, 'tag_regexp': 'V[0-9]{4}[.][0-9]{2}[.][0-9]{2}[a-z]{0,2}', 'logfile': False,
#           'promptonpushpull': True}, 
#       'lgit-pullfrom': {}, 
#       'lgit-files': {}, 
#       'lgit-pullrefspec': {}, 
#       'lgit-pushrefspec': {}, 
#       'lgit-pushrepository': {}
#      }
#    >>> lgitlib.opts["lgit"]["git_rep_root"]
#    '~/gits/'
#    >>> 
#
#  To change options, here is an example:
#     >>> lgitlib.opts["lgit"].update({"git_rep_root": ensure_trailing_slash(fixpath("~/xgits/"))})
#     >>> lgitlib.opts["lgit"]["git_rep_root"]
#     '/Users/rehoot/xgits/'
#     >>> 

opts = {}
#
# flist will contain a code and a path for a working directory,
# where the code serves as the subdirectory for the git repository
# in the ~/gits directory.  Example entry: texmfmain: adsf
flist = {}
pullfromlist = {}
pullrefspeclist = {}
pushrefspeclist = {}
pushrepositorylist = {}
# Default values for the main lgit options
lgitcodes = []
# The safe commands do not change the working or git directories,
# and the dontneedroot extensions might change the git directory
# but not the stored git objects (as best as I can tell).
safecmds = ["blame", "cat-file", "config", "describe", "diff", "diff",
 "difftool", "grep", "help", "log", "ls-files" "rev-parse", "rev-list",
 "send-email", "shortlog", "show", "show-branch", "show-index", 
 "show-ref", "status", "setup", "verify-tag", "whatchanged" ]
#
dontneedroot = []
#
ltx_path_vars = ["TEXMFMAIN", "TEXMFDIST", "TEXMFLOCAL", 
 "TEXMFSYSVAR", "TEXMFSYSCONFIG", "TEXMFVAR", "TEXMFCONFIG",
 "TEXMFHOME"]
#
found_ltx_paths = []
#
def load_cmds():
	print("use load_options instead")

def ensure_trailing_slash(mypath):
	"""Ensure that a string ends with a slash but do not
  add duplicate trailing slashes
	"""
	if mypath[-1:] != "/":
		return mypath + "/"
	else:
		return mypath

def change_git_dir_owner(gitdir):
	reguser = int(os.getenv("SUDO_UID"))
	reggrp = int(os.getenv("SUDO_GID"))
	# return the git directory to be owned by the regular user ID 
	os.system("chown -R " + "%d" % reguser + ":" + "%d" % reggrp 
						+ " " + gitdir )

def load_options():
	"""load_options will read ~/.lgitconf and load values from the
	[lgit] section into the global opts{} dictionary, and will
	also load some global variables.
	"""
	global opts
	global flist
	global pullfromlist
	global pushrefspeclist
	global pullrefspeclist
	global pushrepositorylist
	global CONF_FILE_NAME
	global conf_file_portlist
	global safecmds
	global dontneedroot
	global lgitcodes
	#
	dontneedroot.extend(safecmds)
	dontneedroot.append("tag")
	dontneedroot.append("branch")
	dontneedroot.append("add")
	#
	# Load defaults into lgitcodes, which are options
	lgitcodes.extend([
			["debug_prompt", False],
			["debuglvl", 0],
			["git_rep_root", portpath(["~", "gits"])],
			["logfile", False],
			["promptonpushpull", True],
			["requireroot", True], 
			["tag_regexp", 
				"V2[0-9]{3}[.][0-9]{2}[.][0-9]{2}[a-zA-Z]{0,2}"],
			["unlockgitdir", True]]
	)
	#
	CONF_FILE_NAME = fixpath(portpath(conf_file_portlist))	
	#
	if(os.access(fixpath(CONF_FILE_NAME), os.F_OK)):
		# Create a ConfigParser object:
		o = configparser.ConfigParser()
		#
		# Now read a list of config files (only one file)
		o.read([fixpath(CONF_FILE_NAME)])
		#
		for sect in o.sections():
			# "sect" will contain something like lgit, lgit-files, or 
			# a user-defined pair like usrbin and usrbin-files.
			# First add an empty, nested dictionary
			# in the opts dictionary:
			opts.update({sect:{}})
			# Now process the option depending on option type:
			if(sect.find("-") < 0):
				# This option section is a main entry for option keys
				# that do not contain a dash.
				for m in lgitcodes:
					# parms: configP object, sect, key, default
					my_get_opt(o, sect, m[0], m[1])
			else:
				# This runs for option section names that contain
				# a hyphen, like usrbin-files, lgit-pushrepository...
				for f in o.options(sect):
					my_get_opt(o, sect, f, "")
	else:
		print("The lgit configuration file was not found.")
		yn = yn_input("Do you want to initialize the options? (y/n) ")
		if(yn == "y"):
			setup()
	dprint(5, "lgit", "============================================" 
		" option test:\n" + repr(opts))

def my_get_opt(confp, sect, optkey, default):
	"""This will load the requested option into the globally
	defined 'opts' dictionary. 
	'confp'   is a ConfigParser object.
	'sect'    is the options section code, such as 'lgit' or 'lgit-files'.
	'optkey'  is the option within the specified section.  It can be one 
	          of the hard-coded options like promptonpushpull or a codename
			  for a directory, like texmf-main.
	'default' is the default value for this option.
	"""
	global opts
	global flist
	#
	if(sect.find("-") > 0):
		output_sect = sect[0:sect.index("-")]
	else:
		output_sect = sect
	try:
		q = confp.get(sect, optkey)
	except configparser.NoOptionError:
		print("option not found in the " + sect + " section of the " 
					+ " config file: " + optkey + ". Using default: " + 
					repr(default))
		q = default
	#
	# Perform some translations for booleans:
	if(str(q).upper() in (["T", "TRUE", "Y", "YES"])):
		q = True
	elif(str(q).upper() in (["F", "FALSE", "N", "NO"])):
	   q = False
	elif(q.isdecimal()):
		q = int(q)
	#	
	# Ensure trailing slash on my directories:
	if(optkey in (["git_rep_root"]) \
		or sect.find("-files") > 0 \
		or sect.find("-pushrepository") > 0 \
		or sect.find("-pullfrom") > 0  \
		or sect.find("-pullrefspec") > 0 ):
		q = ensure_trailing_slash(q)
	#	
	if(sect.find("-files") > 0):
		flist.update({optkey:[q, output_sect]})
	elif(sect.find("-pullfrom") > 0):
		pullfromlist.update({optkey:[q, output_sect]})
	elif(sect.find("-pullrefspec") > 0):
		pullrefspeclist.update({optkey:[q, output_sect]})
	elif(sect.find("-pushrefspec") > 0):
		pushrefspeclist.update({optkey:[q, output_sect]})
	elif(sect.find("-pushrepository") > 0):
		pushrepositorylist.update({optkey:[q, output_sect]})
	else:	
		# The opts dictionary contains nested dictionaries
		# keyed by the "options section" name:
		opts[sect].update({optkey:q})
	#
	return(q)

def setup():
	"""Run 'texconfig conf' to find the most important LaTeX
	directories, capture that list, then export 
	default options to a conf file.
	"""
	global bSetupRan
	global found_ltx_paths
	#
	matched_lines = []
	cont = True 
	if(os.access(fixpath(CONF_FILE_NAME), os.F_OK)):
		cont = False
		print("This program will overwrite your lgit options "
					+ "with default settings.")	
		yn = yn_input("\nDo you want to continue? (y/n)")
		if(yn.lower() in (["y"])):
			# Continue and overwrite the existing file
			cont = True
			newname = fixpath(portpath(["~", ".lgitconfBACK"]) + \
					datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
			shutil.copyfile(fixpath(CONF_FILE_NAME), fixpath(newname))
	#
	if(cont):
		# Use the texconfig program to generate a list 
		# of LaTeX directories that should be tracked.
		print("Please wait while the texconfig program scans your "
					+ "LaTeX options and directory tree...")
		srchlist = subprocess.Popen(["texconfig", "conf"], \
		stdout = subprocess.PIPE).communicate()[0]
		#
		q = re.split("\n", srchlist.decode("latin-1"))
		for s in q:
			# Search for the strings in the texconfig output
			# that might be useful.
			tmp = re.match(r"^TEXMF[A-Z]*[=][^{]", s)
			if(tmp != None):
				matched_lines.append(tmp)
		for a_match in matched_lines:
			# The matched lines are in regexp match objects, 
			# not strings.
			tmp = re.split("=", a_match.string)
			if(tmp[0] in (ltx_path_vars)):
				# The input record contains an important
				# LaTeX search path, so add it to the 
				# dictionary for eventual output to the ~/.lgitconf
				# file..
				found_ltx_paths.append([tmp[0], fixpath(tmp[1])])
		#
		for s in q:
			# scan the texconfig output again to look for the
			# entry for mktex.cnf, which is in a different format.
			tmp2 = re.match(r"[^{]+mktex[.]cnf", s)
			if(tmp2 != None):
				found_ltx_paths.append(["mktexcnf", 
					fixpath(os.path.split(tmp2.string)[0])])
		## Check for duplicate paths in lgitfile
		## THIS DOES NOT WORK BECAUSE THE COUNT() FUNC DOES NOT
		## LOOK INIDE NESTED LISTS.
		#for(chckpath in found_ltx_paths):
		#	if(found_ltx_paths.count(chckpath[1]) > 1):
		#		print("Warning.  There are duplicate paths in the "
		#					+ "LaTeX search tree")
		#		print("Review the paths in " + CONF_FILE_NAME + " -- " 
		#					+ chckpath[1])
		export_default_options("lgit")
		load_options()
		create_git_repositories("lgit")
		bSetupRan = True
		print("The options in ~/.lgitconf have been created.  Please review them.")

def create_git_repositories(sect):
	"""During the setup process, use the list of git directory
	names to create the appropirate directories.  The
	'sect' argument is the name assigned to this cluster
	and is entered in the ~/.lgitconf file as a section
	code like: [lgit]
	"""
	global flist
	global opts
	#
	gitroot = ensure_trailing_slash(fixpath(opts[sect]["git_rep_root"]))
	#
	# First see if the root of the new repository
	# exists:
	if(not os.access(gitroot, os.F_OK)):
		# The root repository directory does not exist,
		# Prompt the user and create one.
		print("\nThe lgit repository root directory does not currently "
					+ "exist but will be located here:\n" + gitroot) 
		yn = yn_input("Do you want to create this repository directory?"
					+ " (y/n) ")
		if(yn == "y"):
			os.mkdir(gitroot)
	#
	# Now check for the individual repository directories that
	# will be under the root repository directory:
	for L in flist:
		gitdir = fixpath(gitroot + L)
		if(not os.access(gitdir, os.F_OK)):
			# The directory for this git repository does not exist.
			# Prompt the user and create one if requested.
			print("\nThe following working directory: " + flist[L][0] +  flist[L][1] )
			print("will be associated with a git repository in this " 
						+ "directory:\n" + gitdir + "\nbut the reository directory "
						+ "does not exist.")
			yn = yn_input("Do you want to create this repository directory?"
						+ " y/n) ")
			if(yn == "y"):
				os.mkdir(gitdir)

def export_default_options(sect):
	"""Read the global list of found_ltx_paths and create a 
	ConfigParser object that can be exported as a config file.
	Contents will include the LaTeX working directories and a 
	few basic options.
	"""
	gitroot = ""

	op = configparser.ConfigParser()
	#
	# Create "sections" in the config file, like:
	#    [lgit]
	op.add_section(sect)
	op.add_section(sect + "-files")
	op.add_section(sect + "-pullfrom")
	op.add_section(sect + "-pullrefspec")
	op.add_section(sect + "-pushrefspec")
	op.add_section(sect + "-pushrepository")
	#
	ynq = ""
	while ynq not in ["y"]:
		gitroot = fixpath(input("\nLocation for the collection of all your git repositories (where your backups will be stored)\n" \
									+ "(press ENTER to accept the default of " + portpath(["~", "gits"]) + "): " ))
		ynq = ynq_input("You entered a git repository of: " + gitroot + ".\nDo you want to continue? (y/n/q)")
	if ynq == "q":
	   # force quit
	   sys.exit(-1)


	# Use the lgitcodes list to create default
	# option values.
	for L in lgitcodes:
		op.set(sect, L[0], L[1])
	#	
	for L in found_ltx_paths:
		# Create config file entries for each directory
		# to track, and create blank entries so the
		# user can see where to enter push and pull
		# paths (used by the git push command).
		op.set(sect + "-files", L[0], L[1])
		op.set(sect + "-pullfrom", L[0], ".")
		op.set(sect + "-pullrefspec", L[0], "master:master")
		op.set(sect + "-pushrefspec", L[0], "master:master" )
		op.set(sect + "-pushrepository", L[0], "." )
	#	
	# Apply the override to the git root.
	# opts["lgit"].update({"git_rep_root": ensure_trailing_slash(gitroot) })
	op.set("lgit", "git_rep_root", ensure_trailing_slash(fixpath(gitroot)))
	# Write the config information to a file.
	fd3 = open(fixpath(CONF_FILE_NAME),"w")
	op.write(fd3)
	fd3.close()

def fixpath(thepath):
	"""Expand the ~/ shortcut if present, resolve any links in the path,
	and remove any double slashes from the path
	"""
	return (os.path.normpath(os.path.realpath(os.path.expanduser(
					os.path.expandvars(thepath)))))

def yn_input(prompt):
	"""Prompt the user with the given message and keep prompting 
	until the user enters either 'Y' or 'N' (upper or lower case).
	Return the entered value.
	"""
	yn = input(prompt).lower()
	while (yn not in ("y", "n")):
		yn = input(prompt).lower()
	return(yn)


def ynq_input(prompt):
	"""Prompt the user with the given message and keep prompting 
	until the user enters either 'Y', 'N' or 'Q' (upper or lower case).
	Return the entered value.
	"""
	ynq = input(prompt).lower()
	while (ynq not in ("y", "n", "q")):
		ynq = input(prompt).lower()
	return(ynq)

def portpath(pathL):
	"""Given a list object that contains ordered elemetns of a path 
	or path with filename, join those elements using
	the path separator and return the result.  This might improve
	portability across operating systems.

	Example:
	  portpath(["~","Documents", "myfile.txt"])
	"""
	return(os.path.sep.join(pathL))

def dprint(dbglvl, sectname, msg):
	"""A generic debug print function that checks the debug level
	before printing anything.
	"""
	#
	dlvl = opts[sectname]["debuglvl"]
	if(dlvl >= dbglvl):
		print(msg)
		if(opts[sectname]["debug_prompt"]):
			yn = yn_input("Continue? (y/n")
			if(yn == "n"):
				print("Exiting now.")
	return(0)
	
#if __name__ == '__main__': 
#	main()
