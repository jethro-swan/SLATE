#/usr/bin/bash

SLATE_PID=(`ps ax | grep gunicorn | grep slate | awk '{print $1}'`)
kill -TERM $SLATE_PID
