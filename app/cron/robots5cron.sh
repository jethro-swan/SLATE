#!/bin/bash

for i in {1..12}; do
  /home/slate/SLATE/app/cron/robots_cron.py
  sleep 5
done
