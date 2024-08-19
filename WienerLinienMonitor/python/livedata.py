import pandas as pd
import numpy as np
import urllib.request, json
import time
import datetime

#------------global constants------------------------------------------------------------
#constants
DISPLAY_MODE = 0 #int - 0 or 1, 0 for approximate live in station times, 1 for continous mode
LINES = ["U1","U2","U3","U4","U6"]
STATIONS = {}
STATION_NAME_DICT = {}#keys are DIVA numbers, val are Station Names

TRAIN_IN_STATION_TIME = 30 #seconds ... time the light gets illuminated in a station by a train
TRAIN_DEPARTURE_DELAY_TIME_OFFSET = -15 #seconds ... time the light gets illuminated bevore the train is in station according to SET_OF_DEPARTURES

#API
STATIONS_MEASSURED = ["Landstraße","Westbahnhof","Praterstern"]
MIN_REFRESH_INTERVALL = 45 #seconds, checkforupdate will wait with updating data until this time intervall between updates is reached
MAX_REFRESH_INTERVALL = 180 #seconds
#Departure Data
DEPARTURE_LOOKAHEAD = 2 #how many departures
CUTOFF_EXPIRED_DEPARTURES = -30 #seconds, departures not in list when departure_time lower than this var


time_pd = pd.read_csv("N:\\Projekte\\WienerLinienMonitor\\Fahrtzeiten-auswertung\\Fahrzeiten-von-Stationen.csv",sep=";")
TRAVEL_TIME_LINES = {}

#------------init------------------------------------------------------------------------
def init_STATIONS():
    stations_pd = pd.read_csv("WienerLinienMonitor\\python\\Coordinates.csv",sep=";")
    def stations_of_line(line):
        stations_of_line = []
        for station_diva in stations_pd[line]:
            if(station_diva>0):
                stations_of_line.append(int(station_diva))
        return stations_of_line
    
    for line in LINES:
        STATIONS[line] = np.array(stations_of_line(line))

def init_time_data():
    keys = time_pd.keys()
    for line in LINES:
        for key in keys:
            if(key[:2] == line):
                number_of_stations = STATIONS[line].size
                A = np.zeros(number_of_stations)

                for i in range(number_of_stations):
                    A[i] = time_pd[key].iloc[i]
                TRAVEL_TIME_LINES[key] = A
        
def init_STATION_NAME_DICT():
        stations_pd = pd.read_csv("WienerLinienMonitor\\python\\Coordinates.csv",sep=";")
        for line in LINES:
            for index in range(len(stations_pd[line])):
                diva = stations_pd[line].iloc[index]
                if diva>0: #diva is not nan
                    text = stations_pd["Text"+line].iloc[index]
                    STATION_NAME_DICT[int(diva)] = text.upper()
        

def getStationName(diva):
    return STATION_NAME_DICT[diva]

def getDiva(string):
    return int(list(STATION_NAME_DICT.keys())[list(STATION_NAME_DICT.values()).index(string.upper())])

def getStationIndex(line,station_diva):
    return np.where(STATIONS[line] == station_diva)[0][0]




class LoadData:
    def __init__(self) -> None:
        init_STATIONS()
        init_STATION_NAME_DICT()
        init_time_data()
        
        self.rawdata = self.__generateLiveData()
        self.updateDepartureData()
        pass
        
    def generateAPI_URL(self,station_name_List):
        assert len(station_name_List)>0
        start = "https://www.wienerlinien.at/ogd_realtime/monitor?diva="
        between = "&diva="
        string = start + str(getDiva(station_name_List[0].upper()))
        for name in station_name_List[1:]:
            string += between + str(getDiva(name.upper()))
        return string

    def __generateLiveData(self):
        URL = self.generateAPI_URL(STATIONS_MEASSURED)
        with urllib.request.urlopen(URL) as url:
                data = json.loads(url.read().decode())
        return data
    
    def refreshLiveData(self):
        self.rawdata = self.__generateLiveData()
        self.updateDepartureData()
        self.flag_update_needed = False

    def get_rawdata(self):
        return self.rawdata
    
    def get_SetOfDepartures(self):
        return self.SetOfDepartures
    
    def checkForUpdate(self):
        if(self.seconds_since(self.Ref_Time)<MIN_REFRESH_INTERVALL):
            return
        if(self.flag_update_needed or self.seconds_since(self.Ref_Time)>MAX_REFRESH_INTERVALL):
            self.refreshLiveData()

    def checkForUpdate_get_setOfDepartures(self):
        self.checkForUpdate()
        return self.SetOfDepartures
    def get_Ref_Time(self):
        return self.Ref_Time
    def get_LINES(self):
        return LINES.copy()
#------------DataComuptation-------------------------------------------------------------
    
    def updateDepartureData(self):
        self.SetOfDepartures = {}
        self.Ref_Time =  datetime.datetime.now()
    
        List_of_allStations = self.rawdata["data"]["monitors"]
        for index in range(len(List_of_allStations)):
            LocationStop = List_of_allStations[index]
            station_diva = int(LocationStop["locationStop"]["properties"]["name"])
            if(not station_diva in STATION_NAME_DICT):
                print(f"station {station_diva} not in STATION_NAME_DICT")
                continue
            #get departures from initial station (this "meassured" station)
            for departing_line in LocationStop["lines"]:
                line = departing_line["name"]
                if(not line in LINES):
                    continue
                if(line in self.SetOfDepartures):
                    newLine = self.updateLineArray_mode0(station_diva,departing_line) if DISPLAY_MODE==0 else \
                        self.updateLineArray_mode1(station_diva,departing_line,withprevData=True, prevData=self.SetOfDepartures[line])
                
                    self.SetOfDepartures[line] = self.SetOfDepartures[line] | newLine
                    print(line,getStationName(station_diva),"hahapdppf")
                else:
                    newLine = self.updateLineArray_mode0(station_diva,departing_line) if DISPLAY_MODE==0 else \
                        self.updateLineArray_mode1(station_diva,departing_line)

                    self.SetOfDepartures[line] = newLine
            
        print(f"TIME_REF_DEVIATION:{datetime.datetime.now()-self.Ref_Time}")
        
    def updateLineArray_mode1(self,diva,dep_line_data,withprevData = False, prevData = None):
        line = dep_line_data["name"]
        direction = dep_line_data["direction"] #H for Hin, R for Rück
        
        DepartureSet = prevData if withprevData else {}
        Departures = dep_line_data["departures"]["departure"]
        dep_times = self.departure_countdown_from_station(Departures)

        station_index = getStationIndex(line,diva)
        origin_index = self.get_startstationindex_for_updateFunction(diva,line,direction)
        lookahead_len = abs(station_index-origin_index) + DEPARTURE_LOOKAHEAD
        

        DepArray = np.full((2,lookahead_len),-TRAIN_IN_STATION_TIME)
        if(diva in DepartureSet):
            oldlen = np.shape(DepartureSet[diva])[1]
            if(oldlen<lookahead_len):
                DepArray[:,:oldlen] = DepartureSet[diva][:,:]
            else: DepArray = DepartureSet[diva]

        DepArray_direction_index = 1*(direction == "R")
        print(line,getStationName(diva),direction,"->",dep_times)
        for i in range(min(lookahead_len,np.size(dep_times))):
            DepArray[DepArray_direction_index,i] = dep_times[i]

        DepartureSet[diva] = DepArray
        return DepartureSet

    def updateLineArray_mode0(self,diva,dep_line_data):
        line = dep_line_data["name"]
        DepArray = np.full((len(STATIONS[line]),2,DEPARTURE_LOOKAHEAD),-TRAIN_IN_STATION_TIME)
        direction = dep_line_data["direction"] #H for Hin, R for Rück
        
        Departures = dep_line_data["departures"]["departure"]
        dep_times = self.departure_countdown_from_station(Departures)

        station_index = getStationIndex(line,diva)
        origin_index = self.get_startstationindex_for_updateFunction(diva,line,direction)

        delta_time = TRAVEL_TIME_LINES[line + "von" + str(diva)]

        #looking back in time
        start_index = min(station_index,origin_index)
        stop_index = max(station_index,origin_index) 

        DepArray_second_index = (direction == "R")
        DepArray_number_of_departures = np.shape(DepArray)[2]

        for index in range(start_index,stop_index,1):
            dep_times_station = dep_times - delta_time[index]
            
            if(not np.any(dep_times_station>CUTOFF_EXPIRED_DEPARTURES)):# throws if delta_time[index] is NaN or station data to much behind
                self.flag_update_needed = True
                #print(f"no_pos_val_in_dep_times: Line = {line}, StationIndex = {index}, direction = {direction}\n dep_times_station = {dep_times_station}, CUTOFF = {CUTOFF_EXPIRED_DEPARTURES}")
                continue 
            print("dep",dep_times_station)
            cutoff_expired_dep_index = np.argwhere(dep_times_station>CUTOFF_EXPIRED_DEPARTURES)[0][0]
            for third_index in range(DepArray_number_of_departures):
                if(cutoff_expired_dep_index + third_index<dep_times_station.size):
                    DepArray[index,int(DepArray_second_index),third_index] = dep_times_station[cutoff_expired_dep_index + third_index]     
                
        return DepArray
            
    def get_startstationindex_for_updateFunction(self,diva_meassure_station:int,line_meassured:str,line_direction:str):
        """input:   int diva of meassured station
                    str line meassured
                    str line direction of meassured line
            uses Live_Data to determine the origin station of the trains and then 
            takes the minimum if index_origin_station > index_meassure_station
            (or maximum if index_origin_station < index_meassure_station, that is if range_direction positive) of origin_station 
            and all stations that are being meassured which are on the line_meassured
            and between origin_station and meassure_station
            returns: int index of first station the updateLineArray function should use for computing the live data
        """
        index_meassure_station = getStationIndex(line_meassured,diva_meassure_station)
        
        line_origins = self.get_destinations_from_station_and_line(diva_meassure_station,line_meassured)
        train_origin_str = line_origins[line_direction=="H"] #reverse for origin station
        train_origin_diva = getDiva(train_origin_str)
        index_train_origin = getStationIndex(line_meassured,train_origin_diva)
        
        range_direction = 1-2*(index_train_origin>index_meassure_station)
        L = [index_train_origin]
        for other_meassure_station in STATIONS_MEASSURED:
            other_meassure_station_diva = getDiva(other_meassure_station)
            if(other_meassure_station_diva in STATIONS[line_meassured]): #meassure station relevant... 
                index_other_meassure_station = getStationIndex(line_meassured,other_meassure_station_diva)
                if(index_other_meassure_station in range(index_train_origin,index_meassure_station,range_direction)):
                    L.append(index_other_meassure_station)
        LN = np.array(L)
        #print("LN:",LN)
        return range_direction*np.max(range_direction*LN)
                
    def get_destinations_from_station_and_line(self,station_diva,line_searched):
        """ input: departure data from specific station and line
            uses Live_Data
            returns array of size two and dtype string
                    array[0] ... destination in direction H
                    array[1] ... destination in direction R
        """
        A = ["",""]
        location_stops = self.rawdata["data"]["monitors"]
        Line_destination_data = [] 
        for location_stop in location_stops:
            departing_lines = location_stop["lines"]
            for departing_line in departing_lines:
                if(departing_line["name"] == line_searched):
                    Line_destination_data.append(departing_line)
        
        #print("linedestdata",Line_destination_data)
        for single_destination_data in Line_destination_data:
            
            train_towards = single_destination_data["towards"].strip()
            train_direction = single_destination_data["direction"]
            
            #TODO: check for lines with more than one destination possible (U1,U2)
            
            
            A[train_direction == "R"] = train_towards
            if(A[0]!="" and A[1]!="") :
                #print("found:",A)
                return A
        print("nothing found")#TODO
        pass

        
    def departure_countdown_from_station(self,departures):
        L = []
        for departure in departures:
            dep_time_str = departure["departureTime"]["timePlanned"]
            dep_time = time.strptime(dep_time_str,'%Y-%m-%dT%H:%M:%S.000%z')
            dep_datetime = datetime.datetime.fromtimestamp(time.mktime(dep_time))
            L.append((dep_datetime-self.Ref_Time).total_seconds())
        return np.array(L)
         
    def seconds_since(self,since_time):
        return (datetime.datetime.now()-since_time).total_seconds()

    def updateDisplayData(self):
        """ Format of DepartureData 
            {str "line":{str "station_name":
                nd-array[int station_index][int direction][int rank_of_departure] = int departure_after_reftime_in_seconds, ...}
            shape of nd-array is: (number_of_stations_on_line,2,DEPARTURE_LOOKAHEAD)
            
            returns DisplayData
            Format of DisplayData {str "line":
                nd-array [int station_index][int direction] = int TrainInStation (0 means no, 1 means yes)
                , ...}
        """
        time_now = datetime.datetime.now()
        seconds_since_reftime = (time_now - self.Ref_Time).total_seconds()

        DisplayData = {}
        for line_key in self.SetOfDepartures.keys():
            LineDepartureData = self.SetOfDepartures[line_key] 
            newLineData = self.updateDisplayData_mode0(LineDepartureData,seconds_since_reftime) if DISPLAY_MODE==0 else \
                self.updateDisplayData_mode1(LineDepartureData,seconds_since_reftime)
            DisplayData[line_key] = newLineData
        return DisplayData

    def updateDisplayData_mode1(self):
        #TODO
        pass

    def updateDisplayData_mode0(self,LineDepartureData,seconds_since_reftime):
        number_of_stations = np.shape(LineDepartureData)[0]
        LineDisplayData = np.zeros((number_of_stations,2),dtype = int)
        
        for i,j in np.ndindex(number_of_stations,2):
            arrival_times = LineDepartureData[i,j] - int(seconds_since_reftime) + TRAIN_DEPARTURE_DELAY_TIME_OFFSET
            departure_times = arrival_times + TRAIN_IN_STATION_TIME
            #if(line_key=="U3"):
                #print("print",arrival_times*departure_times)
            if(any(arrival_times*departure_times<0)):
                LineDisplayData[i,j] = 1
        
        return LineDisplayData

    def show_displaydata(self,DisplayData):
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



    

#string time in JSON-Response to datetime obj
def dateTimeFromString(string):
    String_Time = time.strptime(string,'%Y-%m-%dT%H:%M:%S.000%z')
    return datetime.datetime.fromtimestamp(time.mktime(String_Time))




