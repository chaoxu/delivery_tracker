import ups
import yaml
import pprint

def multiple_tracking(ups_conn, tracking_number):
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
  result = ups_conn._transmit_request(tracking_request)
  pprint.pprint(result.dict_response)

with open(r'config.yml') as file:
  # The FullLoader parameter handles the conversion from YAML
  # scalar values to Python the dictionary format
  CONFIG = yaml.load(file, Loader=yaml.FullLoader)

ups_conn = ups.UPSTrackerConnection(CONFIG['UPS_ACCESS_KEY'],
                                    CONFIG['UPS_USER_ID'],
                                    CONFIG['UPS_PASSWORD'])
print(ups.get_tracking_from_reference(ups_conn,"BBY01-806446945906"))

# multiple_tracking(ups_conn, ['1Z804TT30302688134', '1Z804TT30302653564'])
