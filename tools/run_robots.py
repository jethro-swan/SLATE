#!/home/slate/SLATE/venv/bin/python3

import sys
from app.core.flags import set_flag, unset_flag

if sys.argv[1] == "start": # run robots
    set_flag("run_robots")
elif sys.argv[1] == "stop":
    unset_flag("run_robots")
else:
    print("Usage: run_robots start|stop")
