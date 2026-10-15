#!/usr/bin/python
# runs on the player, watches the player's power status as reported by the server
# and sends lirc commands to turn an amp on or off

import socket, select, sys, re, subprocess, uuid, time

SERVER_HOST = "slug"
SERVER_PORT = 9090

RESTART_DELAY = 30
RECONNECT_INTERVAL = 300
DEBUG = False

IRSEND = "/usr/bin/irsend"
REMOTE = "ONKYO_RC-606S"

def log(message, debug_only=False):
  if debug_only and not DEBUG:
    return
  print "[%s] %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), message)


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
  log("Sending LIRC command: %s" % cmd, debug_only=True)
  result = subprocess.call(irsend_cmd.split(' '))
  if result != 0:
    log("irsend exited with status %d" % result)


def subscribe_squeezebox():
  """
  open a socket to the server, watch the power status of the players
  """
  power_pat = r'%s power ([10])' % get_mac()
  regex = re.compile(power_pat)

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  log("Connecting to %s:%d" % (SERVER_HOST, SERVER_PORT), debug_only=True)
  try:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    s.settimeout(2)
    s.connect((SERVER_HOST, SERVER_PORT))
    s.send("subscribe power\n")
  except socket.error, e:
    log("Unable to connect (%s); retrying in %d seconds" % (e, RESTART_DELAY))
    s.close()
    return

  log("Connected; subscribed to power events for %s" % get_mac(), debug_only=True)
  try:
    # Periodically reconnect even if no events arrive. A dropped connection
    # without a TCP close notification would otherwise leave select() blocked.
    while 1:
      read_sockets, write_sockets, error_sockets = select.select(
        [s], [], [], RECONNECT_INTERVAL)

      if not read_sockets:
        log("Refreshing socket connection after %d seconds without data" %
            RECONNECT_INTERVAL)
        return

      for sock in read_sockets:
        if sock == s:
          data = sock.recv(4096)
          if not data:
            # socket probably lost so restart the socket
            log("Lost socket connection; restarting in %d seconds" % RESTART_DELAY)
            return
          else:
            match = regex.search(data)
            if match is not None:
              power_status = match.groups(1)[0]
              log("Received power status: %s" % power_status, debug_only=True)
              if power_status == '1':
                send_lirc('KEY_POWER')
              else:
                send_lirc('KEY_SLEEP')
            else:
              log("Received data with no matching power event: %r" % data,
                  debug_only=True)
  except (socket.error, select.error), e:
    log("Socket error (%s); restarting in %d seconds" % (e, RESTART_DELAY))
  finally:
    s.close()

if __name__ == "__main__":
  if '-d' in sys.argv or '--debug' in sys.argv:
    DEBUG = True
    log("Debug logging enabled")

  # loop forever
  # if the socket expires, restart it
  while 1:
    subscribe_squeezebox()
    time.sleep(RESTART_DELAY)
