#!/home/slate/SLATE/venv/bin/python3
#
# This file is run as a cron task

from app.core.robots import robots_respond

robots_respond()
