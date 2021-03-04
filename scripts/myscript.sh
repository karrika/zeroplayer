#!/bin/bash
fbcp&
sleep 10
echo xset -dpms
echo xset s off
echo xset q
python3 /home/pi/MP3_Player.py
