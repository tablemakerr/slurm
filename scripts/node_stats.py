#!/usr/local/python/3.2/bin/python3

"""
node_stats - A way to get a summary of what each node did the past amount of
time specified by options.

Items include Failed Jobs, Completed Jobs, Quick Jobs (<1hr), Long jobs (>1hr)
most & least used node.

So far this has been meant for Python3 - should be any version.  Some of this
code is re-used from sstats.py

Will expand further as needed

@Version 1.0
@Author tyler

TODO - Add more statements for verbosity()
TODO - More sanity() checks
TODO - Implement -t
"""

### Import commands
import getopt
import subprocess
import sys
import datetime


# Functions
def main():

    # Global Variables
    global SACCT_CMD
    global VERBOSE
    global DATE_STRING
    global LAST_WEEK
    global YESTERDAY
    global SPECIFIC
    global GET_ALL
    global GET_COMPLETED
    global GET_FAILED

    # The command that is the cornerstone of the data for this script.
    SACCT_CMD = '/apps/slurm/default/bin/sacct --format=JobID,User,Account,State,ExitCode,Start,End,Elapsed,NodeList,ElapsedRaw,Partition --allusers --allocations --noheader --state=COMPLETED --parsable2 --starttime='
    

        # Initiate our global values
    GET_ALL         = False
    GET_COMPLETED   = False
    GET_FAILED      = False
    VERBOSE         = False
    YESTERDAY       = False
    LAST_WEEK       = False
    SPECIFIC        = False

    # Parse the command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'acdfhtvw?', ['all', 'completed', 'day', 'failed', 'help', 'time', 'verbose', 'week'])
    except getopt.GetoptError:
        print('Non-existant option....')
        print('')
        usage()
    for opt, arg in opts:
        if opt in ('-h', 'help', '--help', '?', '-?'):
            usage()
        elif opt in ('-a', '--all'):
            GET_ALL = True
        elif opt in ('-c', '--completed'):
            GET_COMPLETED = True
        elif opt in ('-d', '--day'):
            YESTERDAY = True
        elif opt in ('-f', '--failed'):
            GET_FAILED = True
        elif opt in ('-t', '--time'): #NYI
            SPECIFIC = True
            DATE_STRING = arg
        elif opt in ('-v', '--verbose'):
            VERBOSE = True
        elif opt in ('-w', '--week'):
            LAST_WEEK = True

    # Do a sanity check on items we assume should be
    sanity()

    # Run the script.
    get_requested_data()

"""
verbosity(text)

@param text

Takes text as an input, checks if we want to be verbose, and then prints the
string.  A way of pushing out useful information in each function as long as
some output is defined.
"""
def verbosity(text):
    if VERBOSE:
        print(str(text))


"""
sanity()

Checks that the user defined what class of data they want.  We can assume that
without options they want the past 12 hours of data.  However we should not
assume what kind of data they want.  An argument could be made for all, but I'd
rather be explicit for now, so lets bomb out if they don't tell us.

TODO - Ensure provided date with -t option is a valid format for Slurm - YYYY-mm-ddTHH:mm:ss
"""
def sanity():

    # Ensure we have *some* value set for what we're trying to get.c
    if not GET_ALL and not GET_COMPLETED and not GET_FAILED:
        verbosity('You did not specify what class of information you wanted.')
        print('You must specify either, All, Completed, or Failed jobs')
        usage()

    # Check to see we have valid access to Slurm commands
    (SLURM_VERIFY_CODE, STATE_INFO) = subprocess.getstatusoutput('/usr/bin/which /apps/slurm/default/bin/sinfo')
    if SLURM_VERIFY_CODE:
        verbosity("Slurm check exit code: " + str(SLURM_VERIFY_CODE))
        print('No Slurm commands found.  Check PATH &/or Modules')
        usage()


"""
usage()

Prints out information on how to use the script and exits the script.
TODO - Accept EXIT_CODE, but default to 0.
"""
def usage():

    # Print our usage statement
    print('')
    print ('Slurm Stats:')
    print ('Any valid Slurm user should be able to run this command')
    print ('-a/--all         -> Displays all stats that this script gathers')
    print ('-c/--completed   -> Displays information on Completed jobs')
    print ('-d/--day         -> Get stats for the past 24 hours')
    print ('-f/--failed      -> Displays information on Failed jobs')
    print ('-h/?             -> Displays this help message')
    print ('-t/--time        -> !!! NYI !!! Select a specific time interval.  Must use valid Slurm time format')
    print ('-v/--verbose     -> Triggers verbose output.')
    print ('-w/--week        -> Get stats for the past 7 days !!! This could take a while !!!')
    print('')

    # Exit the program
    sys.exit(0)

def get_requested_data():

    if not SPECIFIC:
        DATE = construct_date()
    else:
        DATE = DATE_STRING

    global SLURM_INFO
    SLURM_INFO = run_slurm(DATE)

    verbosity("calculating Job information")
    calculate_job_totals(SLURM_INFO)

    if GET_ALL:
        get_all()
    elif GET_COMPLETED:
        get_completed()
    elif GET_FAILED:
        get_failed()

"""
run_slurm(starttime)

@param starttime

Our function that actually performs the Slurm command.  At this point we've
verified that we indeed have a valid Slurm path.

Within this function, we run our Slurm command, verify the output, and then
loop over the data, separating different parts out into relevant Dictionary
fields.  This should allow us to parse the data we just obtained.

This is done so that Slurm commands are only done once, and we work off the
dataset that was obtained, rather than many many many Slurm commands
"""
def run_slurm(starttime):

    # Finalize our constructed command
    GET_JOB_INFO = str(SACCT_CMD) + str(starttime) + ' --endtime=now'

    print('Requested time interval: ' + str(starttime))

    verbosity("What does our Slurm command look like?")
    verbosity(str(GET_JOB_INFO))

    # Run our Slurm command
    print('Querying Slurm....')
    (EXIT_CODE_RUN, STATE_INFO) = subprocess.getstatusoutput(GET_JOB_INFO)

    if EXIT_CODE_RUN == 0:
        verbosity('Slurm command success')
        verbosity('Successfully gathered State information')

        # Set up local Lists to contain data as we loop through our results
        verbosity('Setting up blank local Lists for parsing')
        jobids      = []
        users       = []
        groups      = []
        states      = []
        exits       = []
        starts      = []
        ends        = []
        elapsed     = []
        nodes       = []
        elapsed_raw = []
        partitions  = []

        # Loop through our results, storing relevant data within each List
        verbosity('Looping through our results and placing into appropriate Lists')
        for line in STATE_INFO.split("\n"):
            jobids.append(line.split("|")[0])
            users.append(line.split("|")[1])
            groups.append(line.split("|")[2])
            states.append(line.split("|")[3])
            exits.append(line.split("|")[4])
            starts.append(line.split("|")[5])
            ends.append(line.split("|")[6])
            elapsed.append(line.split("|")[7])
            nodes.append(line.split("|")[8])
            elapsed_raw.append(line.split("|")[9])
            partitions.append(line.split("|")[10])
        # Take the final results of the Lists and store them within a Dictionary
        verbosity('Constructing data Dictionary')
        RESULT = {
            'JOBID'       : jobids,
            'USERS'       : users,
            'GROUPS'      : groups,
            'STATE'       : states,
            'EXIT'        : exits,
            'START'       : starts,
            'END'         : ends,
            'ELAPSED'     : elapsed,
            'NODES'       : nodes,
            'ELAPSED_RAW' : elapsed_raw,
            'PARTITIONS'  : partitions, 
        }
        return RESULT
    else:
        print('FAILURE: Unable to get Job Status')
        sys.exit(EXIT_CODE_RUN)


"""
most_frequent(LIST)

Taken from online.  A way to find the most common ocurrence of an item in a List

@param LIST - The List we want to examine.

@return common - The most common item
"""
def most_frequent(LIST):
    counter = 0
    common = LIST[0]

    for item in LIST:
        current_count = LIST.count(item)
        if(current_count > counter):
            counter = current_count
            common = item

    return common

"""
unique_nodes(LIST)

Taken from online & modified for my needs.

Takes in a list and creates a new list of each unique item in the parameter list.

@param LIST - The List we want to examine

@return node_list - The list of unique nodes
"""
def unique_nodes(LIST):
    node_list = []

    for node in LIST:
        if node not in node_list:
            node_list.append(node)

    return node_list


""" unique_partitions(LIST)

Taken from online and copied from above so probably should generalize

Takes in a list and creates a new list of each unique item in the parameter list.

@param LIST - The List we want to examine

@return partition_list - The list of unique partitions
"""
def unique_partitions(LIST):
    partition_list = []

    for partition in LIST:
        if partition not in partition_list:
            partition_list.append(partition)

    return partition_list

"""
construct_date()

@return DATE_STRING

Our way of taking canned date parameters and formatting it so that Slurm can
accept.

We are offering:
7d -> 24h -> 12h
"""
def construct_date():

    # 7 days.
    verbosity("Are we looking for last week?")
    if LAST_WEEK:
        verbosity("Setting timestamp to last week")
        timestamp = datetime.datetime.now() - datetime.timedelta(days = 7)

    # 24 hours.
    elif YESTERDAY:
        verbosity("No, are we looking for Yesterday?")
        verbosity("Setting timestamp to Yesterday")
        timestamp = datetime.datetime.now() - datetime.timedelta(days = 1)

    # Default is 12 hours.
    else:
        verbosity("No, we must want the default")
        verbosity("Setting timestamp to 12 hours ago (DEFAULT)")
        timestamp = datetime.datetime.now() - datetime.timedelta(hours = 12)

    verbosity("Construct our DATE_STRING")
    DATE_STRING = timestamp.strftime("%Y-%m-%dT%H:%M:%S")

    return DATE_STRING


"""
"""
def calculate_job_totals(STATE_INFO):
    verbosity('Obtaining Job Completion Stats...')

    # Actual calculations here

    # Job state variables
    global FAILED
    global COMPLETED
    global RUNNING
    global ELIGIBLE
    global CANCELLED
    global TIMEOUT
    global TOTAL

    # Job calculations
    global COMPARISON_TOTAL
    global COMP_RATE
    global FAIL_RATE
    global USER_FAIL
    global GROUP_FAIL
    global EXIT_FAIL
    global E1_FAIL
    global E7_FAIL

    global UNDER_MINUTE
    global UNDER_THIRTY_MINUTES
    global UNDER_HOUR
    global LONG_JOBS
    global MOST_NODE

    # Total amount of jobs based on each newline

    TOTAL = len(STATE_INFO.get('JOBID'))
    verbosity('TOTAL = ' + str(TOTAL))

    # Amount of running jobs
    RUNNING = STATE_INFO.get('STATE').count('RUNNING')

    # Amount of eligible jobs
    ELIGIBLE = STATE_INFO.get('STATE').count('PENDING')

    # Amount of completed jobs
    COMPLETED = STATE_INFO.get('STATE').count('COMPLETED')

    # Amount of cancelled jobs
    CANCELLED = STATE_INFO.get('STATE').count('CANCELLED')

    TIMEOUT = STATE_INFO.get('STATE').count('TIMEOUT')

    # Failed amount of jobs based on MANY criteria
    FAILED = TOTAL - COMPLETED - RUNNING - ELIGIBLE - CANCELLED - TIMEOUT

    # We want to compare rates based on the sum of total jobs
    COMPARISON_TOTAL = FAILED + COMPLETED
    FAIL_RATE = (FAILED/COMPARISON_TOTAL)*100
    COMP_RATE = (COMPLETED/COMPARISON_TOTAL)*100
    USER_FAIL = most_frequent(STATE_INFO.get('USERS'))
    GROUP_FAIL = most_frequent(STATE_INFO.get('GROUPS'))
    EXIT_FAIL = most_frequent(STATE_INFO.get('EXIT'))
    E1_FAIL = STATE_INFO.get('EXIT').count('1:0')
    E7_FAIL = STATE_INFO.get('EXIT').count('7:0')

    MOST_NODE = most_frequent(STATE_INFO.get('NODES'))
    UNDER_HOUR = 0
    for time in STATE_INFO.get('ELAPSED'):
        if "00:" in time:
            UNDER_HOUR += 1

    UNDER_THIRTY_MINUTES = 0
    for job in STATE_INFO.get('ELAPSED_RAW'):
        if int(job) < 1800:
            UNDER_THIRTY_MINUTES += 1

    UNDER_MINUTE = 0
    for job in STATE_INFO.get('ELAPSED_RAW'):
        if int(job) < 60:
            UNDER_MINUTE += 1

    verbosity('UNDER_HOUR: ' + str(UNDER_HOUR))
    verbosity('UNDER_THIRTY_MINUTES: ' + str(UNDER_THIRTY_MINUTES))
    verbosity('UNDER_MINUTE: ' + str(UNDER_MINUTE))

    LONG_JOBS = TOTAL - UNDER_HOUR
    verbosity('LONG JOBS: ' + str(LONG_JOBS))


"""
get_all()

Get all information that we have a method for.  Each function will drop its own
 error code if it fails.  If one fails, we have a script problem or a Slurm
problem so we don't care about continuing.

Exit the script once we got all information
"""
def get_all():
    verbosity('Getting ALL possible information...')
    # Get information on Completed jobs
    get_completed()

    # Get information on Failed jobs
    get_failed()

    # Once we are done with information, cya!
    sys.exit(0)


"""
get_completed(STATE_INFO)

@param STATE_INFO

Get information on completed jobs.  Will run a Slurm command that will gather
stats on completed jobs, list out the amount of failures.
"""
def get_completed():
    verbosity('Obtaining Job Completion Stats...')

    # Actual calculations here

    LIST_OF_PARTITIONS = unique_partitions(SLURM_INFO.get('PARTITIONS'))
    LIST_OF_PARTITIONS.sort()

    print ('############################################')
    print ('Job count by partition')
    print ('If count is zero, partition will not appear in this list')
    print ('____________________________________________')
    
    for partition in LIST_OF_PARTITIONS:
        partition_job_count = SLURM_INFO.get('PARTITIONS').count(partition)

        print (str(partition) + '      ' + str(partition_job_count))

    LIST_OF_NODES = unique_nodes(SLURM_INFO.get('NODES'))
    LIST_OF_NODES.sort()

    print ('')
    print ('############################################')
    print ('Job count by node')
    print ('If count is zero, node will not appear in this list')
    print ('____________________________________________')

    job_count = 0
    for node in LIST_OF_NODES:
        jobs = SLURM_INFO.get('NODES').count(node)

        print (str(node) + '    ' + str(jobs))
        job_count = job_count + jobs
    average = job_count/len(LIST_OF_NODES)
    print ('Number of nodes: ' + str(len(LIST_OF_NODES)))
    print ('____________________________________________')
    print ('Total jobs:            ' + str(job_count))
    print ('Most used node:        ' + str(MOST_NODE))
    print ('Average jobs per node: ' + str(int(average)))
    print ('Amount of jobs <1min:  ' + str(UNDER_MINUTE))
    print ('Amount of jobs <30min: ' + str(UNDER_THIRTY_MINUTES))
    print ('Amount of jobs <1hr:   ' + str(UNDER_HOUR))
    print ('Amount of jobs >1hr:   ' + str(LONG_JOBS))
    print ('')


"""
"""
def get_failed():
    verbosity('Obtaining Job Failure Stats....')

### Call Main
if __name__ == "__main__":
    main()