#!/usr/bin/bash

# Create user "slate":
sudo useradd -M -U -G sudo slate

# Create SLATE data directories:
sudo mkdir -p /var/slate/{data,db,maps,logs}
sudo mkdir -p /var/slate/logs/{collisions,access,errors}
sudo mkdir -p /var/slate/{db,maps}/backups
sudo chown -R slate:slate /var/slate
sudo chmod -R 700 /var/slate
