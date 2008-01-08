#!/usr/bin/env python

# -*- coding: utf-8 -*-

import urllib
import re

class Docomo(object):
  def name(self):
    return 'docomo'

  def url(self):
    return 'http://www.nttdocomo.co.jp/service/imode/make/content/ip/'

  def run(self):
    content = urllib.urlopen(self.url()).read()
    n = self.name()
    return [(ip, n) for ip in re.findall(r'<li>([\d\./]+)</li>', content, re.M)]

class Ezweb(object):
  def name(self):
    return 'ezweb'

  def url(self):
    return 'http://www.au.kddi.com/ezfactory/tec/spec/ezsava_ip.html'

  def run(self):
    content = urllib.urlopen(self.url()).read()
    n = self.name()
    pattern = r'<td>\s*<div class="TableText">([\d\.]+)</div>\s*</td>\s+<td>\s*<div class="TableText">(/\d+)</div>\s*</td>'
    return [(ip + sn, n) for ip, sn in re.findall(pattern, content, re.M)]

class Softbank(object):
  def name(self):
    return 'softbank'

  def url(self):
    return 'http://developers.softbankmobile.co.jp/dp/tech_svc/web/ip.php'

  def run(self):
    content = urllib.urlopen(self.url()).read()
    n = self.name()
    pattern = '<FONT size="2" class="j10".*?>([\d\./]+)</FONT>'
    return [(ip, n) for ip in re.findall(pattern, content, re.M)]

class AirHPhone(object):
  def name(self):
    return 'airhphone'

  def url(self):
    return 'http://www.willcom-inc.com/ja/service/contents_service/club_air_edge/for_phone/ip/'

  def run(self):
    content = urllib.urlopen(self.url()).read()
    n = self.name()
    pattern = '<td align="center" bgcolor="#f5f5f5" width="50%"><font size="2">([\d\./]+)</font></td>'
    return [(ip, n) for ip in re.findall(pattern, content, re.M)]

def get_cidr():
  classes = [Docomo, Ezweb, Softbank, AirHPhone]
  sources = []
  for carrier in classes:
    c = carrier()
    sources += c.run()

  # convert cidr to ipaddress
  import socket, struct
  pat = '([\d\.]+)/(\d+)'
  ranges = []
  for s in sources:
    [(ip, bit)] = re.findall(pat, s[0], re.M)
    ipnum = struct.unpack('>L', socket.inet_aton(ip))[0]
    mask_ed = (1L << (32 - int(bit))) - 1
    mask_st = ~mask_ed
    ip_st = ipnum & mask_st
    ip_ed = ip_st | mask_ed
    ranges.append((ip_st, ip_ed, s[1]))

  # sort
  ranges.sort()

  # merge adjacent range
  preip_st = 0
  preip_ed = 0
  precarr = ''
  merge_st = False
  mranges = []
  i = 0
  while True:
    st = i
    try:
      n = ranges[i + 1]
      while ranges[i][1] + 1 == n[0] and \
            ranges[i][2] == n[2]:
        i += 1
        n = ranges[i + 1]
      mranges.append((ranges[st][0], ranges[i][1], ranges[st][2]))
      i += 1
    except IndexError, e:
      mranges.append((ranges[st][0], ranges[i][1], ranges[st][2]))
      break

  # output php source
  print """<?php
function ip2mobile($ip) {
  $n = sprintf('%u', ip2long($ip));
"""
  output_php(mranges, 0, len(mranges) - 1, 2)
  print """  return 'pc';
}
?>
"""

def output_php(range, st, ed, ind):
  # print st, ed, "\n"
  if st > ed:
    return
  if st == ed:
    print ' ' * ind + 'if ($n >= %d && $n <= %d) {' % (
      range[st][0], range[st][1])
    print ' ' * ind + "  return '%s';" % range[st][2]
    print ' ' * ind + '}'
    return
  b = int((st + ed) / 2)
  print ' ' * ind + 'if ($n < %d) {' % range[b][0]
  output_php(range, st, b - 1, ind + 2)
  print ' ' * ind + '} else if ($n <= %d) {' % range[b][1]
  print ' ' * ind + "  return '%s';" % range[b][2]
  print ' ' * ind + '} else {'
  output_php(range, b + 1, ed, ind + 2)
  print ' ' * ind + '}'

if __name__ == '__main__':
  get_cidr()
