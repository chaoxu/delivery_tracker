import usps
import yaml
import pprint
with open(r'config.yml') as file:
  # The FullLoader parameter handles the conversion from YAML
  # scalar values to Python the dictionary format
  CONFIG = yaml.load(file, Loader=yaml.FullLoader)

usps_conn = usps.USPSTrackerConnection(CONFIG['USPS_USER_ID'],
                                    CONFIG['USPS_SOURCE_NAME'])

pprint.pprint(usps_conn.tracking(['9400111899564256379917']))
