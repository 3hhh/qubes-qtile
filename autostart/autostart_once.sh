#!/bin/bash
#
# qtile autostart script, executed only once after boot at first qtile start
#
# Please do not modify this! Use ~/.config/qtile/autostart_once.sh instead!

#name of this script
SCRIPT_NAME="${BASH_SOURCE[0]##*/}"

#path to the user's autostart_once.sh script
AUTOSTART_USER_SCRIPT="~/.config/qtile/autostart_once.sh"

#don't do anything, if qubes.skip_autostart is set
if grep "qubes.skip_autostart" "/proc/cmdline" ; then
  echo "$SCRIPT_NAME: Found qubes.skip_autostart in the kernel commandline. Not starting anything."
  exit 0
fi

#regular start
echo "$SCRIPT_NAME: Starting up..."

#start all the XFCE *.desktop files, if the user doesn't handle it
if grep "dex-autostart" "$AUTOSTART_USER_SCRIPT" &> /dev/null ; then
  echo "$SCRIPT_NAME: The user executes dex-autostart. Doing nothing..."
else
  #dex tends to screw with pipes, so we don't give it any
  pgrep -fa qui-devices | grep -v pgrep &> /dev/null || dex-autostart -w -a -e XFCE < /dev/null &> /dev/null
fi

echo "$SCRIPT_NAME: All done."
