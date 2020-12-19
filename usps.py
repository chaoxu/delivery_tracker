# Allow getting all tracking numbers from UPS
# forked the code from https://github.com/unicod3/ClassicUPS
import json
import requests
import xmltodict
import pprint
from datetime import datetime
from dict2xml import dict2xml
from utils import take_some_time
DEFAULT_TIME = datetime(1970,1,1,0,0,0).date()
import traceback
import sys
import time

class USPSTrackerConnection(object):
  def __init__(self, user_id, source_name="John Doe"):
    self.user_id = user_id
    self.source_name = source_name
    self.ip_address  = requests.get('https://api.ipify.org').text
    self.delay = 2.0
    self.retry = 2

  def tracking(self, trackingNumbers):
    # split into chunk of 10
    result = []
    limit = 10
    chunked = [trackingNumbers[i:i + limit] for i in range(0, len(trackingNumbers), limit)]
    for chunk in chunked:
      result.extend(self._usps_request(chunk))
    return result

  @take_some_time
  def _usps_request(self, trackingNumbers):
    # a request with at most 10 tracking numbers
    XML = '<TrackFieldRequest USERID="{user_id}">'.format(user_id=self.user_id)
    XML += '<Revision>1</Revision>'
    XML += '<ClientIp>' + self.ip_address + '</ClientIp>'
    XML += '<SourceId>' + self.source_name + '</SourceId>'
    for x in trackingNumbers:
      XML += '<TrackID ID="{trackid}"/>'.format(trackid=x)
    XML += '</TrackFieldRequest>'
    l = []
    try:

      for i in range(self.retry):
        response = requests.get('http://production.shippingapis.com/ShippingAPI.dll?API=TrackV2&XML='+XML).text
        result = xmltodict.parse(response)
        if 'Error' not in result:
          break
        time.sleep(self.delay)

      #pprint.pprint(result)
      z = result['TrackResponse']['TrackInfo']
      if len(trackingNumbers)==1:
        z = [z]
      for x in z:
        tracking_number = x['@ID']
        try:
          status = x['StatusCategory']
          if 'PredictedDeliveryDate' in x:
            eta = datetime.strptime(x['PredictedDeliveryDate'], '%B %d, %Y').date()
          elif status == 'Delivered':
            eta = datetime.strptime(x['TrackSummary']['EventDate'], '%B %d, %Y').date()
          else:
            eta = DEFAULT_TIME
        except:
          status = 'FAIL'
          eta = DEFAULT_TIME
        l.append((tracking_number, status, eta))
    except Exception as e:
      print("FAILURE at request")
      print(XML)
      print(response)
      traceback.print_exc(file=sys.stdout)
      for x in trackingNumbers:
        l.append((x, 'FAIL', DEFAULT_TIME))
    return l
