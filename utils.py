from datetime import datetime
import time

def take_some_time(f):
  def wrapper(*args):
    delay = args[0].delay
    start = datetime.now()
    result = f(*args)
    end = datetime.now()
    diff = end-start
    need_more = delay - diff.total_seconds()
    if need_more > 0:
      time.sleep(need_more)
    return result

  return wrapper
