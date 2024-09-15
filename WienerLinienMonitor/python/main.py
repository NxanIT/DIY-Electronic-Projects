import pandas as pd
import numpy as np
import time
import datetime

import livedata
from livedata import LoadData
from monitor import Monitor


def print_mode1_SetOfDepartures(DepSet):
    print("printing SetOfDepartures [Displaymode == 1]...")
    for line in DepSet.keys():
        
        depLine = DepSet[line]
        for diva_key in depLine.keys():
            print(line,end=" - ")
            print(livedata.getStationName(diva_key)[:3],end="-> ")
            depArray = depLine[diva_key]
            
            print(depArray[0,:],f"\n{line} -",livedata.getStationName(diva_key)[:3] ,end= "<- ")
            print(depArray[1,:])
    


def main():
    t1 = datetime.datetime.now()
    Data = LoadData()
    #print(Data.get_rawdata())
    print(Data.get_Ref_Time())
    print_mode1_SetOfDepartures(Data.get_SetOfDepartures())
    exit()
    Lines = Data.get_LINES()
    #Output_Monitor = Monitor(Lines)
    print(f"init finished, took {datetime.datetime.now()-t1}")

    while(True):
        tia = datetime.datetime.now()
        #d = Data.get_SetOfDepartures()
        #print_mode1_SetOfDepartures(d)
        
        DisplayData = Data.updateDisplayData()
        print(DisplayData)
        #Output_Monitor.lightDisplay(DisplayData)
        Data.show_displaydata(DisplayData)
        tie = datetime.datetime.now()
        if(input(f"calculation took: {tie-tia}write \"stop\" to exit")=="stop"):
            break
    return 0

if __name__ == '__main__':
    main()






