#!/bin/bash

# one liner to get the directory where the script lives
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
USBNAME="/dev/sda1"
MOUNTDIR="/media/usb"
WIFIUSB="$MOUNTDIR/info/wpa_supplicant.conf"
WIFIPI="/etc/wpa_supplicant/wpa_supplicant.conf"

REBOOT=false

python $SCRIPTDIR/flash_on.py
mount $USBNAME $MOUNTDIR

# sleep to ensure the user sees the light on
sleep 2

# transfer the conf file if it exists + is different from the one
# already on the pi
if test -f $WIFIUSB; then
    if ! (cmp -s $WIFIUSB $WIFIPI); then
	cp $WIFIUSB $WIFIPI
	REBOOT=true
    fi
fi

umount $USBNAME
python $SCRIPTDIR/flash_off.py

if $REBOOT; then
    reboot
fi

