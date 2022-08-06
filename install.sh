#!/bin/sh
sudo apt-get update -y
sudo apt-get install -y xvfb
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
sudo apt install -y chromium-chromedriver
sudo apt-get -y install python3-pip
pip3 install -r requirements.txt