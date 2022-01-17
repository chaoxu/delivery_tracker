import dateparser
import requests
import json

def empty_to_none(str):
  if len(str)==0:
    return None
  return str

def fedex_get_time(date, time, gmt):

def fedex_get_display_time(time_str):
  if len(time_str)==0:
    if time_str != 'Pending':
      try:
        return dateparser.parse(time_str)
      except Exception:
        return None
  return None

# given fedex parcels, send them to the fedex API
def fedex_request(parcels):
  # used stuff here https://stackoverflow.com/questions/18817185/parsing-html-does-not-output-desired-datatracking-info-for-fedex
  trackingInfoList = [{'trackNumberInfo': {
    'trackingNumber': parcel.tracking_number
  }
  } for parcel in parcels]

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
  return data

def fedex_info_update(parcels):
  data = fedex_request(parcels)

  for i in range(len(parcels)):
    parcel =  parcels[i]

    info = data['TrackPackagesResponse']['packageList'][i]
    if info['receivedByNm']:
      parcel.signature = info['receivedByNm']
    if info['statusLocationCity']:
      parcel.last_city = info['statusLocationCity']
    if info['pkgLbsWgt']:
      parcel.weight = float(info['pkgLbsWgt'])
    parcel.last_status = info['keyStatus']
    if info["displayShipDateTime"]:
      parcel.shipping_time = dateparser.parse(info["displayShipDateTime"])

    scan_events = info['scanEventList']
    last_event = scan_events[0]
    parcel.last_update_time =  fedex_get_time(last_event['date'], last_event['time'], last_event['gmtOffset'])

    first_event = scan_events[-1]
    parcel.label_creation_time = fedex_get_time(first_event['date'], first_event['time'], first_event['gmtOffset'])

    parcel.estimated_delivery_time = fedex_get_display_time(info["displayEstDeliveryDateTime"])
    parcel.delivery_time = fedex_get_display_time(info["displayActDeliveryDateTime"])