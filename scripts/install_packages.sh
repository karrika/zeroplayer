#!/bin/bash

sudo apt update
sudo apt upgrade
sudo xargs apt -y install < requirement.txt
pip3 install mplayer.py

