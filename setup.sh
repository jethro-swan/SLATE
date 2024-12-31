#!/usr/bin/bash

$INSTANCE = 1

# Create user "slate":
sudo useradd -M -U -G sudo slate

# Add the installing user to the "slate" group:
sudo usermod -a -G slate $USER
#sudo usermod -a -G slate `whoami`

# Create SLATE data directories:
sudo mkdir -p /var/slate/$INSTANCE
sudo mkdir -p /var/slate/$INSTANCE/logs
sudo mkdir -p /var/slate/$INSTANCE/{db,maps}/backups
sudo chown -R slate:slate /var/slate/$INSTANCE
sudo chmod -R 700 /var/slate$/INSTANCE

sudo mkdir -p /srv/slate/$INSTANCE/{export,import}
sudo mkdir -p /srv/slate/$INSTANCE/export/qr_codes
sudo chown -R slate:slate /srv/slate/$INSTANCE
sudo chmod -R 700 /srv/slate/$INSTANCE



#sudo chown -R slate:slate /var/slate
