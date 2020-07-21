#!/bin/bash

# one liner to get the directory where the script lives
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

DATE=$(date +"%Y-%m-%d_%H%M")
raspistill -vf -hf -o $DIR/pictures/$DATE.jpg
python3 $DIR/write_power.py $DIR/pictures/$DATE.jpg >> $DIR/out.log
