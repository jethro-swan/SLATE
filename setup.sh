#!/usr/bin/bash

# Create user "slate":
sudo useradd -M -U -G sudo slate

# Add the installing user to the "slate" group:
sudo usermod -a -G slate $USER
#sudo usermod -a -G slate `whoami`

# Create SLATE data directories:
sudo mkdir -p /var/slate
sudo mkdir -p /var/slate/logs
sudo mkdir -p /var/slate/{db,maps}/backups
sudo chown -R slate:slate /var/slate
sudo chmod -R 700 /var/slate
#sudo chown -R slate:slate /var/slate
