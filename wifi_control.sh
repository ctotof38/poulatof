#!/bin/bash

usage() {
	printf "action on Wifi interface\n"
	printf "Usage: $0 -a|-d|-c [-n <name>] [-t <timeout>]\n"
	printf "   -a : activate\n"
	printf "   -d : deactivate\n"
	printf "   -c : check\n"
	printf "   -n <name> : interface name, default is wlan0\n"
	printf "   -t <timeout> : for check function, wait until timeout the codeExpected. Default is 2\n"
	printf "   -r <codeExpected> : 0=wifi down, 1=wifi up not connected, 2=wifi connected"
	exit 1
}


# check wifi state
#   0 if wifi down
#   1 if wifi up, but not connected
#   2 if wifi up and connected
check_wifi() {
	# return BM, BMU, BMRU according to state of wlan interface
	# B=Broadcast, M=Multicast, U=up, R=Running
	# BM = interface down
	# BMU = interface up, but not connected
	# BMRU = interface up and connected
	if [ $timeout -eq 0 ]
	then
	  code=$(ifconfig -s $interface | sed -n "s/^${interface}.*[0-9] //p" | sed -e 's/BMRU/2/' -e 's/BMU/1/' -e 's/BM/0/')
	  return $code
	else
	  let count=$timeout
	  code=255
	  while [ $code -ne $returnCode -a $count -gt 0 ]
	  do
	    let count=$count-2
	    code=$(ifconfig -s $interface | sed -n "s/^${interface}.*[0-9] //p" | sed -e 's/BMRU/2/' -e 's/BMU/1/' -e 's/BM/0/')
	    sleep 2
	  done
	  return $code
  fi
}

wifi_down() {
	sudo ifconfig $interface down
}

wifi_up() {
	sudo ifconfig $interface up
}

# ----------------------------------------
# main
# ----------------------------------------
interface=wlan0
timeout=0
returnCode=2

if [ $# -eq 0 ]
then
	usage
fi

# read parameters
action=-1
while getopts 'cadn:t:r:' flag; do
	case "${flag}" in
		a) action=0 ;;
		d) action=1 ;;
		c) action=2 ;;
		n) interface="${OPTARG}" ;;
    t) timeout="${OPTARG}" ;;
    r) returnCode="${OPTARG}" ;;
		*) usage ;;
	esac
done

if [ $action -eq -1 ]
then
	# no mandatory parameter
	usage
fi

case $action in
	0) wifi_up ;;
	1) wifi_down ;;
	2) check_wifi ;;
esac


