#!/usr/bin/python
# monitor players for idle status and turn them off if they're just sitting there

import urllib2, BeautifulSoup, pickle, time

class PlayerStatus():
  """ 
  track the status of the players and determine idleness
  """
  fn = os.path.join(os.path.expanduser('~'), '.playerstatus')
  idle_minutes = 30
  statuses = {}

  def __init__(self, idle_minutes = 30):
    self.idle_minutes = idle_minutes

  def save(self):
    """
    save the current statuses
    """
    for self.statuses as s:
      if not 'timestamp' in self.statuses[s]:
        self.statuses[s]['timestamp'] = time.time()
    pickle.dump(self.statuses, open(self.fn, 'wb'))

  def load(self):
    """
    load the pickle
    """
    try:
      self.statuses = pickle.load(open(self.fn, 'rb'))
    except:
      return False
    return True

  def get_macs(self):
    if self.load():
      return self.statuses.keys()
    return None

  def check_idle(self, statuses):
    """
    look at the player statuses, see if any have been idle for a while
    """
    to_be_idled = []
    
    if self.load():
      # there are some prior statuses
      now = time.time()
      for k in statuses:
        if k not in self.statuses:
          self.statuses[k] = statuses[k]

        if statuses[k]['powerStatus'] == 'on' and self.statuses[k]['powerStatus'] == 'on'
          and statuses[k]['playStatus'] == 'stop' and self.statuses[k]['playStatus'] == 'stop'
          and (time.time() - self.statuses[k]['timestamp']) > 60*self.idle_minutes:
            # idle exceeded; return the mac address
            to_be_idled.append(k)
        elif (statuses[k]['powerStatus'] != self.statuses[k]['powerStatus']) 
          or (statuses[k]['playStatus'] != self.statuses[k]['playStatus']):
            # something has changed; update the timestamp
            statuses[k]['timestamp'] = now
        else:
          # no change; keep the old timestamp
          statuses[k]['timestamp'] = cached_statuses[k]['timestamp']

    self.statuses = statuses
    self.save()
    return to_be_idled

class SqueezeComm():
  """
  manage communication with the server
  """
  host = ""
  port = ""

  def __init__(host, port):
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
    return url_fetch("http://%s:%s/status.html%s" % (self.host, self.port, query_params))

  def get_soup(self, mac = None):
    """
    fetch a soupy version of the status page
    """
    query_params = ''
    if mac is not None:
      query_params = "?player=%s" % (mac)
    html = self.fetch_html(query_params)
    return BeautifulSoup.BeautifulSoup(html)

  def get_player_status(mac):
    """
    return current player status given a mac address
    """
    bs = get_soup(mac)
    statuses = bs.findAll('b')

    # statuses will be play, pause, or stop
    return {'playStatus' : statuses[0].text.lower(), 
            'powerStatus': statuses[3].text.lower()}


  def statuses(macs = None):
    """
    return a dictionary of play status for each player
    """
    if macs is None:
      bs = get_soup()
      player_select = bs.find('select', {'name': 'player'})
      macs = [p['value'] for p in player_select.findAll('option')]
    return {mac: get_player_status(mac) for mac in macs}

  def turn_off(mac):
    """
    turn off a player
    """
    query_params = "?player=%s&p0=power&p1=0" % (mac)
    self.fetch_html(query_params)


if __name__ == "__main__":
  PS = PlayerStatus(idle_minutes = 30)
  macs = PS.get_macs()

  SC = SqueezeComm("slug", "9000")
  statuses = SC.statuses(macs)
  idle_macs = PS.check_idle(statuses)

  for mac in idle_macs:
    SC.turn_off(mac)