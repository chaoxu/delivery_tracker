from enum import Enum
import attr
import tracking_url
import datetime

class Carrier(Enum):
  USPS = 'usps'
  UPS = 'ups'
  FEDEX = 'fedex'
  AMAZON = 'amazon'
  UNKNOWN = 'unknown'

class Status(Enum):
  DELIVERED = 'Delivered'
  EXCEPTION = 'Exception'
  IN_TRANSIT = 'In Transit'
  PICKUP = 'Pickup'
  MANIFEST = 'Manifest'
  OUT_FOR_DELIVERY = 'Out for delivery'
  UNKNOWN = 'Unknown'

#DEFAULT_TIME = datetime(1970,1,1,0,0,0).date()
#USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0'


def carrier(x):
  carrier = tracking_url.guess_carrier(x)
  if not carrier or carrier.carrier not in [Carrier.FEDEX, Carrier.UPS, Carrier.FEDEX]:
    if 'TBA' == x[:3]:
      return Carrier.AMAZON
    return Carrier.UNKNOWN
  return carrier.carrier

# this class describes the status of a parcel
@attr.s
class Parcel:
    tracking_number = attr.ib(type=str, default=None)
    carrier = attr.ib(type=str, default=None)
    last_status = attr.ib(type=str, default=None)
    last_update_time = attr.ib(type=datetime, default=None)
    label_creation_time = attr.ib(type=datetime, default=None)
    estimated_delivery_time = attr.ib(type=datetime, default=None)
    shipping_time = attr.ib(type=datetime, default=None)
    delivery_time = attr.ib(type=datetime, default=None)
    signature = attr.ib(type=str, default=None)
    weight = attr.ib(type=float, default=None)
    last_city = attr.ib(type=str, default=None)

    def __attrs_post_init__(self):
      if self.carrier is None:
        self.carrier = carrier(self.tracking_number)