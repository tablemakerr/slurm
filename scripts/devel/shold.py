#!/usr/bin/env python

"""
shold - version written in Python to attempt to better learn the language as 
well to see if this language will be more robust for this kind of task.

@Version 1.0
@Author TB
"""

### Import commands
import getopt
import re
import subprocess
import sys

## Functions
def main():

    ## Global Variables
    global HOLD_USER
    global HOLD = False
    global MAX_JOB_ZERO = 0
    global MAX_JOB_DEFAULT = 50
    global SCONTROL_CMD = '/path/to/slurm/default/bin/scontrol'
    global SACCTMGR_CMD = '/path/to/slurm/default/bin/sacctmgr -i'
    global VERBOSE = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hru:v?", ["user=", "resume", "help", "verbose"])
    except getopt.GetOptError:
        usage()
    for opt, arg in opts:
        if opt in ("-h", "help", "--help", "?", "-?"):
            usage()
        elif opt in ("-u", "--user"):
            HOLD_USER = arg
        elif opt in ("-r", "--resume"):
            HOLD = True
        elif opt in ("-v", "--verbose")
            VERBOSE = True
    sanity()
    hold_user()

def verbosity(text):
    if VERBOSE:
        print str(text)

def sanity():
    # Handle user names that must be in Camel.Case
    userre = re.compile (r"[A-Z]{1}[a-z]*(\.*[A-Z]*)\.[A-Z]{1}[a-z]*", re.I)
    if not userre.match (HOLD_USER):
        print "ERROR!  Invalid user name format.  Must be Camel.Case"
        print "You submitted: " + str(HOLD_USER)
        usage()

def usage():
    print 'Slurm Hold:'
    print 'You must have proper Slurm priviliges in order to run this command'
    print '-h/?             -> Displays this help message'
    print "-r               -> Sets the script to 'Resume' a user's work, effectively setting their MaxJobs to " + str(MAX_JOB_DEFAULT)
    print '-u First.Last    -> The user to hold.  This will effectively set their MaxJobs to ' + str(MAX_JOB_ZERO) + ".  User name must be in Camel.Case"
    print '-v               -> Triggers verbose output.'
    sys.exit(0)

def hold_user():
    verbosity('Working on ' + str(HOLD_USER))
    
    if HOLD:
        MAX_JOB = MAX_JOB_ZERO
        verbosity('Setting MaxJobs to ' + str(MAX_JOB_ZERO))
    else:
        MAX_JOB = MAX_JOB_DEFAULT
        verbosity('Setting MaxJobs to ' + str(MAX_JOB_DEFAULT))
    verbosity ('We are going to set ' + str(HOLD_USER) "'s MaxJobs to " + str(MAX_JOB))
    
    MODIFY_USER = str(SACCTMGR_CMD) + ' modify user ' + str(HOLD_USER) + ' set MaxJobs=' + str(MAX_JOB)
    (EXIT_CODE, SACCTMGR_OUTPUT) = subprocess.getstatusoutput(MODIFY_USER)

    if EXIT_CODE == 0:
        print str(HOLD_USER) + ' modified successfully.  Set MaxJobs to ' + +str(MAX_JOB)
        sys.exit(0)
    else
        print 'SOMETHING WENT WRONG!!!'
        sys.exit(EXIT_CODE)

### Call Main
if __name__ == "__main__":
    main()