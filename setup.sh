#!/usr/bin/bash

# This is the location of the tree cloned from GitHub:
#HUB_ROOT = $1
#HUB_INDEX = $2

#sudo mkdir -p $HUB_ROOT/$HUB_INDEX
#cd $HUB_ROOT/$HUB_INDEX
#git clone https://github.com/jethro_swan/SLATE

#CONSTANTS = $HUB_ROOT/$HUB_INDEX/app/core/constants.py

# The SLATE hub may have an arbitrary number of data sets, each containing its
# own distinct tree. Rollback to an earlier version can be performed only by a
# hub administrator.
DATASET = 0

# Create user "slate":
sudo useradd -M -U -G sudo slate

# Add the installing user to the "slate" group:
sudo usermod -a -G slate $USER
#sudo usermod -a -G slate `whoami`

# Create SLATE data directories:
sudo mkdir -p /var/slate/$DATASET
sudo mkdir -p /var/slate/$DATASET/logs
sudo mkdir -p /var/slate/$DATASET/{db,maps}/backups
sudo chown -R slate:slate /var/slate/$DATASET
sudo chmod -R 700 /var/slate$/DATASET

sudo mkdir -p /srv/slate/$DATASET/{export,import}
sudo mkdir -p /srv/slate/$DATASET/export/qr_codes
sudo chown -R slate:slate /srv/slate/$DATASET
sudo chmod -R 700 /srv/slate/$DATASET






#sudo chown -R slate:slate /var/slate
