# Allow getting all tracking numbers from UPS
# forked the code from https://github.com/unicod3/ClassicUPS
import json
import requests
import xmltodict
import pprint
from datetime import datetime
from dict2xml import dict2xml

status_map = {
  'I': 'In Transit',
  'D': 'Delivered',
  'X': 'Exception',
  'P': 'Pickup',
  'M': 'Manifest'
}
DEFAULT_DATE = datetime(1970,1,1,0,0,0).date()
pprint = pprint.PrettyPrinter(indent=2)
def ups_status(status_code):
  return status_map.get(status_code, 'UNKNOWN')

def get_tracking_from_reference(ups_conn, reference_number):
  tracking_request = {
    'TrackRequest': {
      'Request': {
        'TransactionReference': {
          'CustomerContext': 'Get tracking status',
          'XpciVersion': '1.0',
        },
        'RequestAction': 'Track',
        'RequestOption': 'activity',
      },
      'ReferenceNumber': {
        'Value': reference_number
      },
    },
  }
  l = []
  for x in ups_conn._transmit_request(tracking_request).dict_response['TrackResponse']['Shipment']:
    l.append(x['Package']['TrackingNumber'])
  return l

class UPSError(Exception):
  def __init__(self, message):
    self.message = message

class UPSTrackerConnection(object):
  def __init__(self, license_number, user_id, password):
    self.license_number = license_number
    self.user_id = user_id
    self.password = password

  def _generate_xml(self, url_action, ups_request):
    access_request = {
      'AccessRequest': {
        'AccessLicenseNumber': self.license_number,
        'UserId': self.user_id,
        'Password': self.password,
      }
    }

    xml = u'''
        <?xml version="1.0"?>
        {access_request_xml}

        <?xml version="1.0"?>
        {api_xml}
        '''.format(
      request_type=url_action,
      access_request_xml=dict2xml(access_request),
      api_xml=dict2xml(ups_request),
    )

    return xml

  def _transmit_request(self, ups_request):
    xml = self._generate_xml('track', ups_request)

    resp = requests.post(
      'https://onlinetools.ups.com/ups.app/xml/Track',
      data=xml.replace('&', u'&#38;').encode('ascii', 'xmlcharrefreplace')
    )

    return UPSResult(resp.text)

  def tracking_info(self, tracking_number):
    return TrackingInfo(self, tracking_number)

  def reference_tracking(self, ref_number):
    return get_tracking_from_reference(self, ref_number)

class UPSResult(object):

  def __init__(self, response):
    self.response = response

  @property
  def xml_response(self):
    return self.response

  @property
  def dict_response(self):
    return json.loads(json.dumps(xmltodict.parse(self.xml_response)))

class TrackingInfo(object):

  def __init__(self, ups_conn, tracking_number):
    self.tracking_number = tracking_number

    tracking_request = {
      'TrackRequest': {
        'Request': {
          'TransactionReference': {
            'CustomerContext': 'Get tracking status',
            'XpciVersion': '1.0',
          },
          'RequestAction': 'Track',
          'RequestOption': 'activity',
        },
        'TrackingNumber': tracking_number,
      },
    }

    self.result = ups_conn._transmit_request(tracking_request)
    #pprint.pprint(self.result.dict_response)

  @property
  def last_status(self):
    # Possible Status.StatusType.Code values:
    return self.last_activity['Status']['StatusType']['Code']

  @property
  def last_time(self):
    return datetime.strptime(self.last_activity['Date']+self.last_activity['Time'], '%Y%m%d%H%M%S')

  @property
  def pick_up_date(self):
    return datetime.strptime(self.package['PickupDate'], '%Y%m%d').date()

  @property
  def eta(self):
    if self.delivery_date:
      return self.delivery_date
    if self.rescheduled_delivery_date:
      return self.rescheduled_delivery_date
    if self.scheduled_delivery_date:
      return self.scheduled_delivery_date
    return DEFAULT_DATE
    #pprint.pprint(self.result.dict_response)
    #exit(0)

  @property
  def scheduled_delivery_date(self):
    if 'ScheduledDeliveryDate' in self.package:
      return datetime.strptime(self.package['ScheduledDeliveryDate'], '%Y%m%d').date()
    else:
      return None

  @property
  def usps_tracking(self):
    if 'PackageServiceOptions' in self.package:
      if 'USPSPICNumber' in self.package['PackageServiceOptions']:
        return self.package['PackageServiceOptions']['USPSPICNumber']
    return None

  @property
  def rescheduled_delivery_date(self):
    if 'RescheduledDeliveryDate' in self.package:
      return datetime.strptime(self.package['RescheduledDeliveryDate'], '%Y%m%d').date()
    return None

  @property
  def delivery_date(self):
    if 'DeliveryDate' in self.package:
      return datetime.strptime(self.package['DeliveryDate'], '%Y%m%d').date()
    return None



  @property
  def package(self):
    return self.result.dict_response['TrackResponse']['Shipment']['Package']

  @property
  def last_activity(self):
    return self.package['Activity'][0]