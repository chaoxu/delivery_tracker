import requests
import json
from tabulate import tabulate
from bs4 import BeautifulSoup
import tracking_url
from collections import ChainMap
from datetime import datetime
import dateparser
import ups

DEFAULT_TIME = datetime(1970,1,1,0,0,0)
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0'

class ParcelInfo:
  def __init__(self, ups_conn, delay=0.5):
    self.ups_conn = ups_conn
    self.delay = delay

  @staticmethod
  def unknown_info(trackingNumbers):
    return {x: {'status':'UNKNOWN', 'delivery_time': DEFAULT_TIME}   for x in trackingNumbers}

  def ups_info_helper(self, trackingNumber, raw=False):
    # a single tracking number, it is important since for multiple, the output is different
    record = self.ups_conn.tracking_info(trackingNumber)

    return {'status': ups.ups_status(record.last_status),
     'delivery_time': datetime.combine(record.eta, datetime.min.time())}

  def ups_info(self, trackingNumbers, raw=False):
    return {x:self.ups_info_helper(x, raw) for x in trackingNumbers}

  @staticmethod
  def usps_info_helper(trackingNumber, raw=False):
    s = requests.Session()
    headers = {'User-Agent': USER_AGENT}
    r = s.get('http://tools.usps.com/go/TrackConfirmAction.action?tLabels='+trackingNumber, headers=headers)

    soup = BeautifulSoup(r.content , 'html.parser')

    delivery_class = soup.findAll("div", {"class": "delivery_status"})[0]

    status = delivery_class.findAll("strong")[0].get_text()
    time = ' '.join(delivery_class.findAll("div", {"class": "status_feed"})[0].findAll("p")[0].get_text().split())

    delivery_time = dateparser.parse(time)

    if status not in ['Delivered','Delivered to Agent']:
      delivery_time = DEFAULT_TIME

    result = {'status': status,
              'delivery_time': delivery_time}
    return result

  @staticmethod
  def usps_info(trackingNumbers, raw=False):
    return {x:ParcelInfo.usps_info_helper(x, raw) for x in trackingNumbers}

  @staticmethod
  def fedex_info(trackingNumbers, raw=False):
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

    if(raw):
      print(json.dumps(data, indent=2))

    result = {}
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

      result[number] = {'status': status,
                        'delivery_time': delivery_time}
    return result

  # input is a list of tracking numbers

  def get_tracking(self, xs):
    f={'usps': self.usps_info,
    'ups': self.ups_info,
    'fedex': self.fedex_info,
    'unknown': self.unknown_info,
    'amazon': self.unknown_info,
    }
    d = {}
    info = {}
    for x in xs:
      if self.carrier(x) not in d:
        d[self.carrier(x)] = []
      d[self.carrier(x)].append(x)

    dd = dict(ChainMap(*[f[y](d[y]) for y in d.keys()]))

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
