#!/bin/bash

FILE=../door_manage.tgz

rm -f $FILE
tar czf $FILE wifi_control.sh watchdog.sh simulator/*.py elements/*.py door_management.sh door_management.py chicken*.json door_daemon.sh
if [ $? -eq 0 ]
then
	echo "$FILE generated"
else
	echo "problem to create $FILE"
fi

