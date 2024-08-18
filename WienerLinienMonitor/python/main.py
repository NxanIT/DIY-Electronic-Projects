import pandas as pd
import numpy as np
import urllib.request, json
import time
import datetime
from datetime import datetime #TODO: rewrite code to not use it


from livedata import LoadData
from monitor import Monitor
#global constants
#constants
TRAIN_IN_STATION_TIME = 30 #seconds ... time the light gets illuminated in a station by a train
TRAIN_DEPARTURE_DELAY_TIME_OFFSET = -15 #seconds ... time the light gets illuminated bevore the train is in station according to SET_OF_DEPARTURES

def updateDisplayData(ref_time:time,DepartureData):
    """ Format of DepartureData 
        {str "line":{str "station_name":
            nd-array[int station_index][int direction][int rank_of_departure] = int departure_after_reftime_in_seconds, ...}
        shape of nd-array is: (number_of_stations_on_line,2,DEPARTURE_LOOKAHEAD)
        
        returns DisplayData
        Format of DisplayData {str "line":
            nd-array [int station_index][int direction] = int TrainInStation (0 means no, 1 means yes)
            , ...}
    """

    time_now = datetime.now()
    seconds_since_reftime = (time_now - ref_time).total_seconds()

    DisplayData = {}
    for line_key in DepartureData.keys():
        LineDepartureData = DepartureData[line_key] #dict
        number_of_stations = np.shape(LineDepartureData)[0]
        LineDisplayData = np.zeros((number_of_stations,2),dtype = int)
        
        for i in range(number_of_stations):
            for j in range(2):
                arrival_times = LineDepartureData[i,j] - seconds_since_reftime + TRAIN_DEPARTURE_DELAY_TIME_OFFSET
                departure_times = arrival_times + TRAIN_IN_STATION_TIME
                #if(line_key=="U3"):
                    #print("print",arrival_times*departure_times)
                if(any(arrival_times*departure_times<0)):
                    LineDisplayData[i,j] = 1
        DisplayData[line_key] = LineDisplayData
    return DisplayData

def show_displaydata(DisplayData):
    keys = DisplayData.keys()
    lengths = {}
    for line in keys:
        lengths[line] = np.shape(DisplayData[line])[0]
        print(line,end="\t")
    print()
    max_len = max([lengths[line] for line in lengths])
    for index in range(max_len):
        for line in keys:
            if(lengths[line]>index):
                print(DisplayData[line][index],end="\t")
            else: print("-----",end="\t")
        print()



        


def main():
    Data = LoadData()
    DepData = Data.get_SetOfDepartures()
    Lines = Data.get_LINES()
    #Output_Monitor = Monitor(Lines)
    while(True):
        ref_time = Data.get_Ref_Time()
        DisplayData = updateDisplayData(ref_time,DepData)
        #Output_Monitor.lightDisplay(DisplayData)
        show_displaydata(DisplayData)
        if(input("write \"stop\" to exit")=="stop"):
            break
    return 0

if __name__ == '__main__':
    main()






