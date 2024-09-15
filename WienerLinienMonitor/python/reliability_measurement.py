from datetime import datetime
import time
import numpy as np
import pandas as pd
import urllib.request,json

from Conversions import FetchData

MEASSURED_STATIONS = ["Landstraße","Ottakring"]
DELAY_BETWEEN_REQUESTS = 60 #seconds, keep above 10
NUMBER_OF_REQUESTS = 10


def main():
    Fe = FetchData(do_not_fetch=True)
    URL = Fe.generateAPI_URL(MEASSURED_STATIONS)
    Lines = Fe.getLINES()
    assert(DELAY_BETWEEN_REQUESTS>10)
    for request_id in range(NUMBER_OF_REQUESTS):
        with urllib.request.urlopen(URL) as url:
                data = json.loads(url.read().decode())
        #print(data)
        Fe.updateDepartures(data)
        Fe.getDisplayData().printDepartures()
        exit()
        time.sleep(DELAY_BETWEEN_REQUESTS)
    pass

if __name__=="__main__":
    main()
