from tabulate import tabulate

def print_result(d):
  table = [[x, y['carrier'], y['status'], y['delivery_time']] for (x,y) in d]
  print(tabulate(table))

def print_tracking(parcel_object, xs):
  print_result(parcel_object.get_tracking(xs))