#!/usr/bin/python
# runs on the player, watches the player's power status as reported by the server
# and sends lirc commands to turn an amp on or off

import socket, select, sys, re, subprocess, uuid, time

SERVER_HOST = "slug"
SERVER_PORT = 9090

PLAYER_MAC = get_mac()

RESTART_DELAY = 30

IRSEND = "/usr/bin/irsend"
REMOTE = "ONKYO_RC-606S"

def get_mac():
  """
  get the mac address, used by squeezeserver to identify the player
  """
  mac = uuid.getnode()
  return '%3A'.join(("%012x" % mac)[i:i+2] for i in range(0, 12, 2))

def send_lirc(cmd):
  """
  send an IR command out, using the shell
  """
  irsend_cmd = "%s SEND_ONCE %s %s" % (IRSEND, REMOTE, cmd)
  subprocess.call(irsend_cmd.split(' '))


def subscribe_squeezebox():
  """
  open a socket to the server, watch the power status of the players
  """
  power_pat = r'%s power ([10])' % PLAYER_MAC
  regex = re.compile(power_pat)

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.settimeout(2)

  s.connect((SERVER_HOST, SERVER_PORT))
  s.send("subscribe power\n")

  # loop until the socket expires
  while 1:
    read_sockets, write_sockets, error_sockets = select.select([s] , [], [])

    for sock in read_sockets:
      if sock == s:
        data = sock.recv(4096)
        if not data:
          # socket probably lost so restart the socket
          print "Lost socket connection; restarting in %d seconds" % RESTART_DELAY
          return
        else:
          match = regex.search(data)
          if match is not None:
            power_status = match.groups(1)[0]
            if power_status == '1':
              send_lirc('KEY_POWER')
            else:
              send_lirc('KEY_SLEEP')

if __name__ == "__main__":
  # loop forever
  # if the socket expires, restart it
  while 1:
    subscribe_squeezebox()
    time.sleep(RESTART_DELAY)