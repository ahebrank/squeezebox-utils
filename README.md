# Squeezebox Utilities

Miscellaneous utilities (mostly having to do with power status) for Squeezebox players.

## watchpower

This script runs on a player and queries the server for its own power status.  When a power change event is noted, it sends the relevant LIRC command to an IR flasher (to turn on or turn off an amplifier).

## watchidle

Intended to be run on a cron, this script checks whether individual players have been idle (i.e., power on but stopped) for more than a certain number of minutes.  If so, the script triggers a power-off event for that player.

(You're probably better off using Jason Holtzapple's helpful plugin PowerSave for this -- it will detect idle state from the server, and power off the player. Then `watchpower` above can trigger an external action.)
