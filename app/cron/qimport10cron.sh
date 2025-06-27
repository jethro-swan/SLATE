#!/bin/bash
for i in {1..6}; do
  /home/slate/SLATE/app/cron/qimport.py
  sleep 10
done
