#!/usr/bin/bash

for f in `ls *.py`
do
#    grep 'import' $f > calls/$f
    grep 'import' $f | grep '^[^#]' | sort | uniq > calls/$f
done
