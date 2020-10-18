#!/bin/bash

# where the shell is
cd $(dirname $0)
HOME_SHELL=$(pwd)

cd $HOME_SHELL >/dev/null
source venv/bin/activate

python $HOME_SHELL/door_management.py
