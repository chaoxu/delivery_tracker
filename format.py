from tabulate import tabulate
import parcel_info

def print_result(d):
  table = [[x, y['carrier'], y['status'], y['delivery_time']] for (x,y) in d.items()]

  print(tabulate(sorted(table, key=lambda x: x[3], reverse=True)))

# this is the most important function
def print_tracking(xs):
  print_result(parcel_info.get_tracking(xs))