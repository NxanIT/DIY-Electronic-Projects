import pandas as pd
import numpy as np
import urllib.request, json
import time
import datetime
from datetime import datetime #TODO: rewrite code to not use it


from livedata import LoadData
#global constants

#GPIO
#constants
TRAIN_IN_STATION_TIME = 30 #seconds ... time the light gets illuminated in a station by a train
TRAIN_DEPARTURE_DELAY_TIME_OFFSET = -15 #seconds ... time the light gets illuminated bevore the train is in station according to SET_OF_DEPARTURES
#seconds ... offset gets added to localtime, pos. value decreases localTime, therefore train arrives later and departs later
PINS_LINE_SELECT = {"U1":14,"U2":15,"U3":18,"U4":25,"U5":8,"U6":7}
PIN_SDO = 12
PIN_CLK = 16
PIN_OE_NOT = 20
PIN_LATCH = 21
SHIFT_REGISTER_SIZE = 48

def main():
    Data = LoadData()
    DepData = Data.get_SetOfDepartures()
    print(DepData)
    return 0

if __name__ == '__main__':
    main()




        





