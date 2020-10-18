#!/bin/bash

# where the shell is
cd $(dirname $0)
HOME_SHELL=$(pwd)

cd $HOME_SHELL >/dev/null
source venv/bin/activate

nohup $HOME_SHELL/door_management.sh > /tmp/door.log 2>&1 &

