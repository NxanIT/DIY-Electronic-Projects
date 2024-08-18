import pandas as pd
import numpy as np
import datetime
import main

class monitor:

    #------------GPIO-----------------------------------------------------------------------

    def Display(self):
        loops_without_update = 0
        data = None
        for i in range(100):
            
            """Format of station data {"line":{"station_name":[DepartureTimes], ...}, ...}
            """

            #check data
            update_needed = False
            #if in any station there is no data for departures after the current time, the flag update_needed is set True
            #load new data if necesarry and ok to do so
            
            #update lightning state of leds
            self.updateDisplayData(data)
            self.lightDisplay(self.DisplayData) #may need a dedicated thread
            loops_without_update += 1
        pass

    def updateDisplayData(self,ref_time,DepartureData):
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
                    arrival_times = LineDepartureData[i,j] - seconds_since_reftime + main.TRAIN_DEPARTURE_DELAY_TIME_OFFSET
                    departure_times = arrival_times + main.TRAIN_IN_STATION_TIME
                    #if(line_key=="U3"):
                        #print("print",arrival_times*departure_times)
                    if(any(arrival_times*departure_times<0)):
                        LineDisplayData[i,j] = 1
            DisplayData[line_key] = LineDisplayData
        self.DisplayData = DisplayData

    

