#!/usr/bin/python
# monitor players for idle status and turn them off if they're just sitting there

import urllib2, BeautifulSoup, re

SERVER_HOST = "slug"
SERVER_PORT = "9000"

def url_fetch(url):
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

def get_soup(mac = None):
  """
  fetch a soupy version of the status page
  """
  query_params = ''
  if mac is not None:
    query_params = "?player=%s" % (mac)
  html = url_fetch("http://%s:%s/status.html%s" % (SERVER_HOST, SERVER_PORT, query_params))
  return BeautifulSoup.BeautifulSoup(html)

def get_player_status(mac):
  """
  return current player status given a mac address
  """
  bs = get_soup(mac)
  statuses = bs.findAll('b')

  return {'playStatus' : statuses[0].text.lower(), 
          'powerStatus': statuses[3].text.lower()}


def get_player_statuses():
  """
  return a dictionary of play status for each player
  """
  bs = get_soup()
  player_select = bs.find('select', {'name': 'player'})
  macs = [p['value'] for p in player_select.findAll('option')]
  return {mac: get_player_status(mac) for mac in macs}