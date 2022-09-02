#!/usr/bin/perl -w
use strict;
use Getopt::Long;
use File::Basename;
use Time::HiRes qw{time alarm};

# Functions
sub usage;
sub check_pid;
sub check_fs;
sub check_memory;
sub check_moab;
sub check_torque;
sub runexec;
sub logit;

# constants
my $CC_LIST="-c tyler\@mail.com";
my $TO_LIST=root\@mail.com";
my $TIMESTAMP=`date '+%Y-%m-%d %H:%M:%S'`;
my $HOSTNAME=(split(/\./, `hostname`))[0];
my $SUBJECT="$HOSTNAME SLURM SCHEDULER STATUS: $TIMESTAMP UTC";


use constant SLURMCTLD_PID_FILE => "/var/run/slurm/slurmctld.pid";
use constant SLURM_CMDS_TIMEOUT => 600;
use constant COMMAND_TIMEOUT => 240; # in seconds
use constant MEMORY_LOW => 65536;  # in kB
use constant DISKSPACE_LOW => 90;  # in % full

#my $BASEDIRMOAB="/opt/moab";
#my $BASEDIRTORQUE="/usr/local/sbin";
#my $STARTCMDMOAB="$BASEDIRMOAB/moabd";
#my $STARTCMDTORQUE="$BASEDIRTORQUE/pbs_server";
my $TMPFILE="/tmp/.check_scheduler.txt";
my $version="1.2";

# variables
my $help=0;

sub usage {
  printf("\nUSAGE:\n");
  printf("%s -h \n", basename($0));
  printf("\n   Version: $version\n\n");
  printf("  -h              : help\n");
  printf("\n");
}

if(!GetOptions(
               'h|?' => \$help
          )) {
  &usage;
  exit 1;
}

if($help) {
  &usage;
  exit 0;
}

sub runexec {

  my $cmd=shift(@_);
  my $out=0;

  eval {
      local $SIG{ALRM} = sub { die "alarm\n" };
      alarm COMMAND_TIMEOUT;
      $out=`$cmd`;
      alarm 0;
      chomp($out);
  };
  return $out;

}

sub check_pid {

  my $rval=0;
  my $pid_file=shift(@_);

  unless (-f $pid_file )
  {
    logit("$pid_file: No such file!\n");
    return 0;
  }

  #my $pid=runexec("ps -ef | grep $process_string | grep -v grep | awk '{print \$2}'");
  my $pid=runexec("cat $pid_file");
  chomp($pid);

  $rval = kill(0,$pid) if $pid;

  return $rval;
}

sub check_memory {

  my $mem=runexec("cat /proc/meminfo | grep MemFree | awk '{print \$2}'");
  return "WARNING: low on memory ($mem)" if $mem < MEMORY_LOW;

  return "";
}

sub check_fs {

  my $fs_string=shift(@_);
  my $out;

  # check if mounted
  my $mount=runexec("cat /proc/mounts | awk '{print \$2}' | grep ^$fs_string\$");
  return "$fs_string is not mounted" unless $mount;

  # check if stale
  $out =runexec("readlink -f $fs_string 2>&1");
  return "$fs_string readlink failed: $out" if (($? >> 8) != 0);

  if (! chdir($fs_string))
  {
     $out=$!;
     return "$fs_string chdir failed: $out";
  }
  $out=runexec("ls -f $fs_string 2>&1");
  return "$fs_string ls failed: $out" if (($? >> 8) != 0);

  # check if almost full
  $out=runexec("df -kP $fs_string | tail -1 | awk '{print \$5}' | sed s/%//");
  return "$fs_string full $out%" if $out > DISKSPACE_LOW;

  # any other checks for the filesystem?

  return "";
}

sub check_slurmctld {

  my $out;

  # There is no sense of 'pause' within slurm so a check for pausing is not useful

  # Ensure slurm.conf exists
  $out=runexec("ls /apps/slurm/default/etc/slurm.conf");
  return "SLURM ERROR: /apps/slurm/default/etc/slurm.conf does not exist" unless $out;

  # Ensure munge.key exists
  $out=runexec("ls /etc/munge/munge.key");
  return "SLURM ERROR: /etc/munge/munge.key does not exist" unless $out;

  # Ensure we have at least one compute node configured
  $out=runexec("/apps/slurm/default/bin/sinfo -N | grep -v STATE | wc -l");
  if (defined $out & $out ne "" ) {
    return "SLURM ERROR: sinfo failure (Check /apps mount) OR no nodes configured! (check slurm.conf)" if $out == 0;
  }

  # Ensure that we have some jobs running
  $out=runexec("/apps/slurm/default/squeue | grep -v JOBID | wc -l");
  if (defined $out & $out ne "") {
    return "SLURM ERROR: squeue failure (Check /apps mount) OR no jobs queued" if $out < 1;
  }

  # Ensure SLURM is scheduling Jobs
  # Dunno a good check for this yet

  return "";

}

sub check_moab {

  my $out;

  # check to see if moab is scheduling jobs
  $out=runexec("/opt/moab/bin/mdiag --timeout=" . SLURM_CMDS_TIMEOUT . " -R | grep 'p-006' | grep Active");
  return "MOAB WARNING:scheduling turned off" unless $out;

  return "";
}

sub logit {

  my $msg=shift(@_);

  open OUT, ">>$TMPFILE" or die "unable to open $TMPFILE for writing\n";
  print OUT "$msg";
  close OUT;

}

###################################################################################
# main
###################################################################################

# unlink tmp file
unlink $TMPFILE if -f $TMPFILE;

# ----------------- #
# system checks
# ----------------- #
# check filesystems
my $stat=check_fs("/");
if ($stat ne "") {
   logit("$stat\n");
}
$stat=check_fs("/home");
if ($stat) {
   logit("$stat\n");
}
# App required for SLURM functionality
$stat=check_fs("/apps");
if ($stat) {
  logit("$stat\n");
}
# check free memory
$stat=check_memory();
if ($stat) {
   logit("$stat\n");
}

# ----------------- #
# slurm
# ----------------- #
# check pid
$stat=check_pid(SLURMCTLD_PID_FILE);
if ($stat == 0) {
   logit("SLURM ERROR: slurmctld not running\n");
}

# check moab
$stat=check_slurmctld();
if ($stat ne "") {
   logit("$stat\n");
}

if (-f $TMPFILE) {
   logit("PLEASE contact the sysadmin for $HOSTNAME asap\n");
   runexec("cat $TMPFILE | mail -s \"$SUBJECT\" $CC_LIST $TO_LIST");
}
