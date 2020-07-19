import requests
import json
from tabulate import tabulate
from bs4 import BeautifulSoup
import tracking_url
from collections import ChainMap
from datetime import datetime

DEFAULT_TIME = datetime(1970,1,1,0,0,0)
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0'


def unknown_info(trackingNumbers):
  return {x: {'status':'UNKNOWN', 'delivery_time': DEFAULT_TIME}   for x in trackingNumbers}

def ups_info_helper(trackingNumber, raw=False):
  # a single tracking number, it is important since for multiple, the output is different
  headers = {
    'content-type': 'application/json',
    'User-Agent': USER_AGENT
  }
  body =  {
                        'Locale': 'en_US',
                        'Requester': 'UPSHome',
                        'TrackingNumber': [trackingNumber]
                        }

  r = requests.post('https://wwwapps.ups.com/track/api/Track/GetStatus?loc=en_US',
                    headers = headers,
                    data =  json.dumps(body)
                    )

  data = r.json()
  number = trackingNumber
  info   = data["trackDetails"][0]
  if info["packageStatus"]=='Delivered':
    delivery_time = info["deliveredDate"]+" "+info["deliveredTime"]
  else:
    delivery_time = info["scheduledDeliveryDate"]+" 9:00 PM"
  delivery_time = delivery_time.replace('.','')
  delivery_time = datetime.strptime(delivery_time, '%m/%d/%Y %I:%M %p')

  result = {'status': info["packageStatus"],
       'delivery_time': delivery_time}
  if(raw):
    print(json.dumps(data, indent=2))
  return result

def ups_info(trackingNumbers, raw=False):
  return {x:ups_info_helper(x, raw) for x in trackingNumbers}

def usps_info_helper(trackingNumber, raw=False):
  s = requests.Session()
  headers = {'User-Agent': USER_AGENT}
  r = s.get('http://tools.usps.com/go/TrackConfirmAction.action?tLabels='+trackingNumber, headers=headers)

  soup = BeautifulSoup(r.content , 'html.parser')

  delivery_class = soup.findAll("div", {"class": "delivery_status"})[0]

  status = delivery_class.findAll("strong")[0].get_text()
  time = ' '.join(delivery_class.findAll("div", {"class": "status_feed"})[0].findAll("p")[0].get_text().split())

  delivery_time = datetime.strptime(time, '%B %d, %Y at %I:%M %p')

  if status not in ['Delivered','Delivered to Agent']:
    delivery_time = DEFAULT_TIME

  result = {'status': status,
            'delivery_time': delivery_time}
  return result

def usps_info(trackingNumbers, raw=False):
  return {x:usps_info_helper(x, raw) for x in trackingNumbers}

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


  result = {}
  for i in range(len(trackingNumbers)):
    number = trackingNumbers[i]
    info   = data['TrackPackagesResponse']['packageList'][i]
    delivery_time = info["displayEstDeliveryDateTime"]
    if len(delivery_time)<1: 
      delivery_time = info["displayActDeliveryDateTime"]

    if delivery_time != 'Pending':
      delivery_time = datetime.strptime(delivery_time, '%m/%d/%Y %I:%M %p')
    else:
      delivery_time = DEFAULT_TIME

    result[number] = {'status': info['keyStatus'],
                      'delivery_time': delivery_time}
  if(raw):
    print(json.dumps(data, indent=2))
  return result

# input is a list of tracking numbers
def get_tracking(xs):
  f={'usps': usps_info,
  'ups': ups_info,
  'fedex': fedex_info,
  'unknown': unknown_info
  }
  d = {}
  info = {}
  for x in xs:
    if carrier(x) not in d:
      d[carrier(x)] = []
    d[carrier(x)].append(x)

  dd = dict(ChainMap(*[f[y](d[y]) for y in d.keys()]))

  output = {}
  for x in xs:
    z = dd[x]
    z['carrier'] = carrier(x) 
    output[x] =  z 
  return output

def carrier(x):
  carrier = tracking_url.guess_carrier(x)
  if not carrier or carrier.carrier not in ['usps','ups','fedex']:
    return 'unknown'
  return carrier.carrier 