import requests
import json
from tabulate import tabulate
from bs4 import BeautifulSoup
import tracking_url
from collections import ChainMap
from datetime import datetime
import dateparser
import ups
import pprint
import time
from utils import take_some_time

DEFAULT_TIME = datetime(1970,1,1,0,0,0).date()
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0'

class ParcelInfo:
  def __init__(self, ups_conn, usps_conn, delay=2.0):
    self.ups_conn = ups_conn
    self.usps_conn = usps_conn
    self.delay = delay

  @staticmethod
  def unknown_info(trackingNumbers):
    return {x: {'status':'Unknown', 'delivery_time': DEFAULT_TIME}   for x in trackingNumbers}

  @take_some_time
  def ups_info_helper(self, trackingNumber):
    # a single tracking number, it is important since for multiple, the output is different
    record = self.ups_conn.tracking_info(trackingNumber)
    return trackingNumber, ups.ups_status(record.last_status), datetime.combine(record.eta, datetime.min.time())

  def ups_info(self, trackingNumbers):
    result = []
    for x in trackingNumbers:
      try:
        info = self.ups_info_helper(x)
      except:
        info = (x, 'FAILED', DEFAULT_TIME)
      result.append(info)
    return result

  def usps_info(self, trackingNumbers):
    return self.usps_conn.tracking(trackingNumbers)

   # input is a list of tracking numbers, at most 30
  @take_some_time
  def fedex_info_helper(self, trackingNumbers):
    # used stuff here https://stackoverflow.com/questions/18817185/parsing-html-does-not-output-desired-datatracking-info-for-fedex
    trackingInfoList = [{'trackNumberInfo': {
         'trackingNumber': x
      }
      } for x in trackingNumbers]

    data = requests.post('https://www.fedex.com/trackingCal/track', data={
        'data': json.dumps({
            'TrackPackagesRequest': {
              'trackingInfoList': trackingInfoList
            }
        }),
        'action': 'trackpackages',
        'locale': 'en_US',
        'format': 'json',
        'version': 99
    }).json()

    result = []
    for i in range(len(trackingNumbers)):
      number = trackingNumbers[i]
      info   = data['TrackPackagesResponse']['packageList'][i]
      status = info['keyStatus']
      delivery_time = info["displayEstDeliveryDateTime"]
      if len(delivery_time)<1:
        delivery_time = info["displayActDeliveryDateTime"]

      if delivery_time != 'Pending':
        delivery_time = dateparser.parse(delivery_time)
      else:
        delivery_time = DEFAULT_TIME
      result.append((number, status, delivery_time))
    return result

  def fedex_info(self, trackingNumbers):
    # don't ask for too many tracking numbers, chunk into size of 30 each
    result = []
    limit = 30
    chunked = [trackingNumbers[i:i + limit] for i in range(0, len(trackingNumbers), limit)]
    for chunk in chunked:
      result.extend(self.fedex_info_helper(chunk))
    return result

  def get_tracking(self, x):
    return (self.get_trackings([x]))[0]

  # input is a list of tracking numbers
  def get_trackings(self, xs):
    f={'usps': self.usps_info,
    'ups': self.ups_info,
    'fedex': self.fedex_info,
    'unknown': self.unknown_info,
    'amazon': self.unknown_info,
    }
    d = {}
    for x in xs:
      if self.carrier(x) not in d:
        d[self.carrier(x)] = []
      d[self.carrier(x)].append(x)

    results = []
    for carrier, trackingNumbers in d.items():
      print(carrier, trackingNumbers)
      results.extend((f[carrier])(list(set(trackingNumbers))))

    dd = {}
    for tracking, status, eta in results:
      dd[tracking] = {'status': status,
                      'eta': eta}

    output = []
    for x in xs:
      z = dd[x]
      z['carrier'] = self.carrier(x)
      output.append((x,z))
    return output

  @staticmethod
  def carrier(x):
    carrier = tracking_url.guess_carrier(x)
    if not carrier or carrier.carrier not in ['usps','ups','fedex']:
      if 'TBA' == x[:3]:
        return 'amazon'
      return 'unknown'
    return carrier.carrier
