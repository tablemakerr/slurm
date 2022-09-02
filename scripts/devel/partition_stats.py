#/usr/bin/python3

"""
partition_stats - A way to get a summary of what each partition handles in the 
past amount of time specified by options.

At this point we're only really worried about overall throughput of each
partition.  Breakdown of jobs is already handled for us in a separate script.

@Version 1.0
@Author tyler
"""

### Import commands
import getopt
import subprocess
import sys
import datetime

# Functions
def main():