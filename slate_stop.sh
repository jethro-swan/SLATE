#/usr/bin/bash

SLATE_PID=(`ps ef | grep gunicorn | grep SLATE | grep ' Sl ' | awk '{print $1}'`)
echo $SLATE_PID

#kill -TERM $SLATE_PID

