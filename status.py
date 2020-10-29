import format
import parcel_info
import ups
import yaml
import sys

with open(r'config.yml') as file:
  # The FullLoader parameter handles the conversion from YAML
  # scalar values to Python the dictionary format
  CONFIG = yaml.load(file, Loader=yaml.FullLoader)

ups_conn = ups.UPSTrackerConnection(CONFIG['UPS_ACCESS_KEY'],
                                    CONFIG['UPS_USER_ID'],
                                    CONFIG['UPS_PASSWORD'])
parcel_object = parcel_info.ParcelInfo(ups_conn)


print(parcel_object.get_tracking([sys.argv[1]]))
