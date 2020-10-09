#!/bin/bash

mkdir -p ~/.fonts
if [ ! -e kg-defying-gravity-bounce.zip ]; then
    wget https://www.wfonts.com/download/data/2014/08/09/kg-defying-gravity-bounce/kg-defying-gravity-bounce.zip
fi
if [ -e kg-defying-gravity-bounce.zip ]; then
    unzip kg-defying-gravity-bounce.zip KGDefyingGravityBounce.ttf -d ~/.fonts
fi
if [ ! -e victoria_4.zip ]; then
    wget https://www.fontpalace.com/zip/victoria_4.zip
fi
if [ -e victoria_4.zip ]; then
    unzip victoria_4.zip VictoriaDemo.ttf -d ~/.fonts
fi
cp dotmatrx.ttf ~/.fonts
fc-cache -v -f
