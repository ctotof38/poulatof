#!/bin/bash

FILE=../door_manage.tgz

rm -f $FILE
tar czf $FILE simulator/*.py elements/*.py door_management.* email_start.py chicken.json
if [ $? -eq 0 ]
then
	echo "$FILE generated"
else
	echo "problem to create $FILE"
fi

