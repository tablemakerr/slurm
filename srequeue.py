#!/usr/bin/env python

"""
srequeue - version written in Python to attempt to better learn the language as 
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
    global ALL = True
    global REQUEUE_USER
    global SCONTROL_CMD = '/path/to/slurm/default/bin/scontrol'
    global SCONTROL_REQUEUE = str(SCONTROL_CMD) + " requeue"
    global SQUEUE_CMD = '/path/to/slurm/default/bin/squeue --state=running -o %A -h'
    global SHOLD_CMD = '/path/to/slurm/scripts/shold'
    global SLURM_JOB_LIST = ''
    global VERBOSE = False
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ahu:v?", ["user=", "resume", "help", "verbose", "all"])
    except getopt.GetOptError:
        usage()
    for opt, arg in opts:
        if opt in ("-h", "help", "--help", "?", "-?"):
            usage()
        elif opt in ("-u", "--user"):
            All = False
            REQUEUE_USER = arg
        elif opt in ("-a", "--all"):
            All = True
        elif opt in ("-v", "--verbose")
            VERBOSE = True
    sanity()
    requeue()

def verbosity(text):
    if VERBOSE:
        print str(text)

def sanity():
    # Handle Camel.Case
    userre = re.compile (r"[A-Z]{1}[a-z]*(\.*[A-Z]*)\.[A-Z]{1}[a-z]*", re.I)
    
    if not userre.match (REQUEUE_USER):
        print "ERROR!  Invalid user name format.  Must be Camel.Case"
        print "You submitted: " + str(REQUEUE_USER)
        usage()

def usage():
    print 'Slurm Requeue:'
    print 'You must have proper Slurm priviliges in order to run this command'
    print '-a               -> Requeue ALL running jobs in the system.'
    print '-h/?             -> Displays this help message'
    print '-u First.Last    -> The user whose jobs will be requeued.  User name must be in Camel.Case'
    print '-v               -> Triggers verbose output.'
    sys.exit(0)

def requeue():
    SLURM_JOB_LIST = subprocess.getoutput(SQUEUE_CMD)

    if !SLURM_JOB_LIST:
        print "Job list is empty, no jobs to requeue"
        sys.exit(0)
    
    verbosity ("Requeueing jobs")
    for job in SLURM_JOB_LIST
        print "Attempting to requeue job " + str(job)
        REQUEUE_CMD = str(SCONTROL_CMD) + " " + str(job)
        (EXIT_CODE, SCONTROL_OUTPUT) = subprocess.getstatusoutput(REQUEUE_CMD)
        if !EXIT_CODE
            print str(job) + " has been requeued successfully!"
            print ""
        else
            print "FAILURE: " + str(job) + " could not be requeueud!  Please inform user."
            print str(SCONTROL_OUTPUT)

    print "All jobs have been requeueud!"


def warning_message():
    if ALL:
        print ""
        print "#################### WARNING ####################"
        print "# THIS WILL REQUEUE ALL CURRENTLY RUNNING JOBS  #"
        print "#      ENSURE THAT YOU WERE DIRECTED BY AN      #"
        print "#     ADMINISTRATOR BEFORE YOU EXECUTE THIS     #"
        print "#    OR THAT YOU HAVE NOTICED AN ISSUE FIRST    #"
        print "#                                               #"
        print "#       THIS DOES NOT PAUSE THE SCHEDULER       #"
        print "#################### WARNING ####################"
        print ""
        print "Did you pause the scheduler too?"
        print ""
        query_string="REQUEUE ALL Running work?"
    else:
        print ""
        query_string="REQUEUE USER " + str(REQUEUE_USER) + "'s work?"

    query_yes_no(query_string)

def query_yes_no(question, default="no"):
    valid = {"yes": True, "y": True, "ye": True,
             "Y": True, "Ye": True, "YE": True, 
             "YES": True, "NO": False, "no": False,
             "N": False, "n": False, "No": False, "nO": False}
    
    if default is None:
        prompt = " [y/n]"
    elif default == "yes":
        promt = " [Y/n]"
    elif default == "no":
        prompt = " [y/N]"
    else:
        raise ValueError("invalid default answer '%s'" & default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == "":
            sys.exit(0)
        elif choice in valid:
            requeue()
        else:
            sys.stdout.write("Please enter either yes or no")

### Call Main
if __name__ == "__main__":
    main()