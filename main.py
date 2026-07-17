import threading
import api_request
from process_acquisition import process_acquisition
from queue import Queue

q = Queue()

thread_api = threading.Thread(target=api_request.api_worker, args=(q,),)
thread_acquisition = threading.Thread(target=process_acquisition,args=(q,))

thread_acquisition.start()
thread_api.start()








