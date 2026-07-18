import threading
import time
from queue import Queue

import api_request
from process_acquisition import process_acquisition


queue = Queue()

api_thread = threading.Thread(
    target=api_request.api_worker,
    args=(queue,),
    daemon=True
)
acquisition_thread = threading.Thread(
    target=process_acquisition,
    args=(queue,),
    daemon=True
)

acquisition_thread.start()
api_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
