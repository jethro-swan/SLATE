#!/usr/bin/bash

# This is the location of the tree cloned from GitHub:

##HUB_DATA_ROOT = $1    # This the root data tree for this

##HUB_INDEX = $2        # Each SLATE or NESTS hub is given a unique identifier in
##                      # a shared data base. For the time being, this is simply
##                      # entered manually at the time of installation.
##
##LOCAL_HUB_NUMBER = $3 #
##HUB_PORT = "8000" + $LOCAL_HUB_NUMBER   # ports: 8000, 8001, 8002, ...
##                                        # allocated to each instance running in
##
HUB_MODE="slate_simple"                              # its own VM.
HUB_USER="slate"
HUB_GROUP="www-data"
##HUB_INSTALLATION=$1
##HUB_DOMAIN="lrc.org.uk"
##HUB_SUBDOMAIN="$HUB_INSTALLATION.$HUB_DOMAIN"
##HUB_URL="https://$HUB_SUBDOMAIN"

# The values are nox

#export HUB_USER
#export HUB_GROUP
#export HUB_INSTALLATION
#export HUB_DOMAIN
#export HUB_SUBDOMAIN
#export HUB_URL

echo "FLASK_APP=slate.py" > .flaskenv
echo "HUB_MODE=$HUB_MODE" >> .flaskenv
echo "HUB_USER=$HUB_USER" >> .flaskenv
echo "HUB_GROUP=$HUB_GROUP" >> .flaskenv
##echo "HUB_INSTALLATION=$HUB_INSTALLATION" >> .flaskenv
##echo "HUB_DOMAIN=$HUB_DOMAIN" >> .flaskenv
##echo "HUB_SUBDOMAIN=$HUB_SUBDOMAIN" >> .flaskenv
##echo "HUB_URL=$HUB_URL" >> .flaskenv




#sudo mkdir -p $HUB_ROOT/$HUB_INDEX
#cd $HUB_ROOT/$HUB_INDEX
#git clone https://github.com/jethro_swan/SLATE

#CONSTANTS = $HUB_ROOT/$HUB_INDEX/app/core/constants.py

# The SLATE hub may have an arbitrary number of data sets, each containing its
# own distinct tree. Rollback to an earlier version can be performed only by a
# hub administrator.
DATASET="000"

# Create user "slate":
sudo useradd -M -U -G sudo slate

# Add the installing user to the "slate" group:
sudo usermod -a -G slate $USER
#sudo usermod -a -G slate `whoami`

# Create SLATE data directories:
sudo mkdir -p /var/slate/$DATASET
sudo mkdir -p /var/slate/$DATASET/logs
#sudo mkdir -p /var/slate/$DATASET/{db,maps}/backups
sudo mkdir -p /var/slate/$DATASET/temp
sudo mkdir -p /var/slate/$DATASET/imports
sudo mkdir -p /var/slate/$DATASET/flags
sudo mkdir -p /var/slate/$DATASET/img
sudo mkdir -p /var/slate/$DATASET/backups
sudo chown -R slate:slate /var/slate/$DATASET
#sudo chmod -R 700 /var/slate/$DATASET
sudo chmod -R 775 /var/slate/$DATASET

##sudo mkdir -p /srv/slate/$DATASET/{export,import}
##sudo mkdir -p /srv/slate/$DATASET/export/qr_codes
##sudo chown -R slate:slate /srv/slate/$DATASET
##sudo chmod -R 700 /srv/slate/$DATASET

sudo ln -sf /var/slate/$DATASET /var/slate/active

sudo chown -R slate:slate /var/slate

# Create systemd service:

##sudo touch slate.service
##
##sudo echo "After=network.target\n\n" > slate.service
##sudo echo "[Service]\n" >> slate.service
##sudo echo "User=slate\n" >> slate.service
##sudo echo "Group=www-data\n" >> slate.service
##sudo echo "WorkingDirectory=/home/slate/SLATE/app\n" >> slate.service
##sudo echo "Environment=\"PATH=/home/slate/SLATE/venv/bin\"\n" >> slate.service
##sudo echo "ExecStart=/bin/bash -c " >> slate.service
##sudo echo "'source /home/slate/SLATE/venv/bin/activate; " >> slate.service
##sudo echo "/home/slate/SLATE/venv/bin/" >> slate.service
##sudo echo "gunicorn -w 4 --bind 0.0.0.0:8000 slate/app'\n" >> slate.service
##sudo echo "Restart=always\n" >> slate.service
##sudo echo "RestartSec=2\n\n" >> slate.service
##sudo echo "[Install]\n" >> slate.service
##sudo echo "WantedBy=multi-user.target\n" >> slate.service
##
##sudo cp slate.service /etc/systemd/system/
