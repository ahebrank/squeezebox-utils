#!/usr/bin/python
# monitor players for idle status and turn them off if they're just sitting there

import os, urllib2, BeautifulSoup, pickle, time

class PlayerStatuses:
  """
  macs -> status objects
  provide an interface for the current status of the players
  """
  statuses = {}

  def get(self, mac):
    if mac in self.statuses:
      return self.statuses[mac]
    return None

  def set(self, mac, status):
    self.statuses[mac] = status

  def set_status(self, mac, power, play):
    self.statuses[mac] = {
      'powerStatus': power,
      'playStatus': play
    }

  def set_time(self, mac, tm):
    if mac in self.statuses:
      self.statuses[mac]['timestamp'] = tm

  def keys(self):
    return self.statuses.keys()

  def dump(self, fn):
    for s in self.statuses:
      if not 'timestamp' in self.statuses[s]:
        self.statuses[s]['timestamp'] = time.time()
    pickle.dump(self.statuses, open(fn, 'wb'))
    return True

  def load(self, fn):
    try:
      self.statuses = pickle.load(open(fn, 'rb'))
    except:
      return False
    return True

  def is_on(self, mac):
    return self.get_power(mac) == 'on'

  def is_stopped(self, mac):
    return self.get_play(mac) == 'stop'

  def get_power(self, mac):
    return self.get_status(mac, 'powerStatus')

  def get_play(self, mac):
    return self.get_status(mac, 'playStatus')

  def get_time(self, mac):
    return self.get_status(mac, 'timestamp')

  def get_status(self, mac, key):
    if not key in ['powerStatus', 'playStatus', 'timestamp']:
      return None
    if not mac in self.statuses:
      return None
    return self.statuses[mac][key]

  def is_idle(self, mac, idle_minutes):
    return ((time.time() - self.statuses[mac]['timestamp']) > 60*idle_minutes)


class SqueezeComm:
  """
  manage communication with the server
  """
  host = ""
  port = ""

  def __init__(self, host, port):
    self.host = host
    self.port = port

  def url_fetch(self, url):
    """
    wrap urllib to get a URL
    """
    try:
      response = urllib2.urlopen(url)
      resp_code = response.getcode()
    except:
      return None

    if (resp_code == 200):
      return response.read()
    return None

  def fetch_html(self, query_params):
    return self.url_fetch("http://%s:%s/status.html%s" % (self.host, self.port, query_params))

  def get_soup(self, mac = None):
    """
    fetch a soupy version of the status page
    """
    query_params = ''
    if mac is not None:
      query_params = "?player=%s" % (mac)
    html = self.fetch_html(query_params)
    return BeautifulSoup.BeautifulSoup(html)

  def get_player_status_markup(self, mac):
    """
    return current player status given a mac address
    """
    bs = self.get_soup(mac)
    return bs.findAll('b')

  def check_statuses(self):
    """
    return a dictionary of play status for each player
    """
    bs = self.get_soup()
    player_select = bs.find('select', {'name': 'player'})
    macs = [p['value'] for p in player_select.findAll('option')]
    statuses = PlayerStatuses()
    for mac in macs:
      status_markup = self.get_player_status_markup(mac)
      statuses.set_status(mac, power=status_markup[3].text.lower(), play=status_markup[0].text.lower())
    return statuses

  def turn_off(self, mac):
    """
    turn off a player
    """
    query_params = "?player=%s&p0=power&p1=0" % (mac)
    self.fetch_html(query_params)


class CheckStatus:
  """ 
  handle the logic of checking idleness between last check and current status
  """
  status_fn = os.path.join(os.path.expanduser('~'), '.playerstatus')

  def check_idle(self, current, idle_minutes = 30):
    """
    look at the player statuses, see if any have been idle for a while
    """
    to_be_turned_off = []
    
    last = PlayerStatuses()
    if last.load(self.status_fn):
      # there are some prior statuses
      now = time.time()
      for k in current.keys():
        if k not in last.keys():
          continue

        if ( current.is_on(k) and last.is_on(k) and
          current.is_stopped(k) and last.is_stopped(k) and
          last.is_idle(k, idle_minutes) ):
            # idle exceeded; return the mac address
            to_be_turned_off.append(k)
        elif ( (current.get_power(k) != last.get_power(k)) or
          (current.get_play(k) != last.get_play(k)) ):
            # something has changed; update the timestamp
            current.set_time(k, now)
        else:
          # no change; keep the old timestamp
          current.set_time(k, last.get_time(k))

    # pickle the current status
    statuses.dump(self.status_fn)
    return to_be_turned_off


if __name__ == "__main__":
  S = CheckStatus()

  SC = SqueezeComm("slug", "9000")
  statuses = SC.check_statuses()
  idle_macs = S.check_idle(statuses, idle_minutes = 30)

  for mac in idle_macs:
    print "Turning off idle %s" % (mac)
    SC.turn_off(mac)