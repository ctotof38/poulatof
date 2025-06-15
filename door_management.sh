#!/usr/bin/env bash

# where the shell is
cd $(dirname $0)
HOME_SHELL=$(pwd)

cd $HOME_SHELL >/dev/null
source venv/bin/activate

INTERFACE="wlan0"
TIMEOUT=10
INTERVAL=3

for i in $(seq 1 $TIMEOUT); do
    ip -br a show "$INTERFACE" | grep -q "UP" && break
    echo "$(date '+%Y/%m/%d %H:%M:%S') :  wait $INTERFACE is UP"
    sleep "$INTERVAL"
done

echo none |sudo tee /sys/class/leds/ACT/trigger >/dev/null
echo 0 |sudo tee /sys/class/leds/ACT/brightness >/dev/null

python $HOME_SHELL/email_start.py $*
python $HOME_SHELL/door_management.py $*
