#!/bin/bash

# ------------------------------------------------
# this program check the file created by the automatic
# door open/close: /tmp/watchdog_hen.txt
# This file contains time in seconds, updated each 5 minutes
# by default
# if current date it greater than 600 seconds, we consider
# the program out. So, reboot the system
# ------------------------------------------------

MAX_DELTA=600

hen_program=$(cat /tmp/watchdog_hen.txt 2>/dev/null)
if [ $? -ne 0 ]
then
  # program not started, check next time
  exit
fi

current_date=$(date -u '+%s')
delta=$(expr $current_date - $hen_program)

if [ $delta -gt $MAX_DELTA ]
then
  /sbin/shutdown -r 0
fi
