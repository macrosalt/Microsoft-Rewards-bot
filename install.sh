#!/bin/sh
sudo apt-get update -y
sudo apt-get install -y xvfb
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
sudo apt install -y chromium-chromedriver
sudo apt-get -y install python3-pip
sudo pip3 install -r requirements.txt
sudo pip3 uninstall --yes chardet
sudo pip3 uninstall --yes urllib3
sudo pip3 install --upgrade requests --no-input
sudo touch accounts.json