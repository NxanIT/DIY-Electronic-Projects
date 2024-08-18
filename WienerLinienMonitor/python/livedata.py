import pandas as pd
import numpy as np
import urllib.request, json
import time
import datetime


LINES = ["U1","U2","U3","U4","U6"]
STATIONS = {}
STATION_NAME_DICT = {}#keys are DIVA numbers, val are Station Names
#API
STATIONS_MEASSURED = ["Landstraße","Westbahnhof","Praterstern"]
#Departure Data
DEPARTURE_LOOKAHEAD = 2 #how many departures
CUTOFF_EXPIRED_DESTINATIONS = -30 #seconds, departures not in list when departure_time lower than this var
SET_OF_DEPARTURES = {}

time_pd = pd.read_csv("N:\\Projekte\\WienerLinienMonitor\\Fahrtzeiten-auswertung\\Fahrzeiten-von-Stationen.csv",sep=";")
TRAVEL_TIME_LINES = {}

#------------init-----------------------------------------------------------------------
def init_STATIONS():
    def stations_of_line(line):
        stations_of_line = []
        stations_pd = pd.read_csv("WienerLinienMonitor\\python\\Coordinates.csv",sep=";")
        
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
        

def init_SET_OF_DEPARTURES():
    for line in LINES: #setup dictionary
        SET_OF_DEPARTURES[line] = np.zeros((len(STATIONS[line]),2,DEPARTURE_LOOKAHEAD)) 
        #axis0...station, axis1...direction(index0..forwards,index1..back), axis2...next departures

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
        init_SET_OF_DEPARTURES()
        init_time_data()
        
        self.rawdata = self.__generateLiveData()
        self.init_setOfDepartures()
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
    def get_rawdata(self):
        return self.rawdata
    def get_SetOfDepartures(self):
        return self.SetOfDepartures
    def get_Ref_Time(self):
        return self.Ref_Time
    def get_LINES(self):
        return LINES.copy()
    #------------DataComuptation------------------------------------------------------------

    def init_setOfDepartures(self):
        S = {}
        for line in LINES: #setup dictionary
            S[line] = np.zeros((len(STATIONS[line]),2,DEPARTURE_LOOKAHEAD)) 
            #axis0...station, axis1...direction(index0..forwards,index1..back), axis2...next departures
        self.SetOfDepartures = S
    
    def updateDepartureData(self):
        self.Ref_Time =  datetime.datetime.now()
    
        List_of_allStations = self.rawdata["data"]["monitors"]
        for index in range(len(List_of_allStations)):
            LocationStop = List_of_allStations[index]
            station_diva = int(LocationStop["locationStop"]["properties"]["name"])
            Station_in_list = station_diva in STATION_NAME_DICT
            if(Station_in_list):
                #get departures from initial station (this "meassured" station)
                for departing_line in LocationStop["lines"]:
                    line = departing_line["name"]
                    if(line in LINES):
                        LineArray = self.SetOfDepartures[line]
                        #print(Returned_Set)
                        #print(LineArray.shape)
                        self.SetOfDepartures[line] = self.updateLineArray(station_diva,departing_line,LineArray)
            
        print(f"TIME_REF_DEVIATION:{datetime.datetime.now()-self.Ref_Time}")
        

    def updateLineArray(self,diva,dep_line_data,DepArray):
        line = dep_line_data["name"]
        direction = dep_line_data["direction"] #H for Hin, R for Rück
        destination = dep_line_data["towards"].strip() #strip needed for diva conversion later
        
        
        Departures = dep_line_data["departures"]["departure"]
        dep_times = self.departure_countdown_from_station(Departures)
        
        #should be unused
        #line_destinations = get_destinations_from_station_and_line(diva,line)
        #Train_origin_str = line_destinations[direction == "R"] #indexes 0 if direction == H, 1 otherwise
        
        station_index = getStationIndex(line,diva)
        #print(line, "->",destination,dep_times)
        
        #should be unused
        #destination_diva = getDiva(destination) #das funkt nicht imma
        #destination_index = np.where(STATIONS[line] == destination_diva)[0][0]
        origin_index = self.get_startstationindex_for_updateFunction(diva,line,direction)

        delta_time = TRAVEL_TIME_LINES[line + "von" + str(diva)]

        #looking back in time
        #print(getStationName(diva),line,destination,station_index,f"from{origin_index}")
        start_index = min(station_index,origin_index)
        stop_index = max(station_index,origin_index) 

        DepArray_second_index = (direction == "R")
        DepArray_number_of_departures = np.shape(DepArray)[2]

        for index in range(start_index,stop_index,1):
            dep_times_station = dep_times - delta_time[index]
            
            if(np.any(dep_times_station>CUTOFF_EXPIRED_DESTINATIONS)):
                cutoff_expired_dep_index = np.argwhere(dep_times_station>CUTOFF_EXPIRED_DESTINATIONS)[0][0]
                
                for third_index in range(DepArray_number_of_departures):

                    if(cutoff_expired_dep_index + third_index<dep_times_station.size):
                        DepArray[index,int(DepArray_second_index),third_index] = dep_times_station[cutoff_expired_dep_index + third_index]
                        #print(f"val_added origin_station_index = {station_index}, Line = {line}, StationIndex = {index}, direction = {direction}\n{index,int(DepArray_second_index),third_index}")
            #else:     # throws if delta_time[index] is NaN or station data to much behind
                #print(f"no_pos_val_in_dep_times: Line = {line}, StationIndex = {index}, direction = {direction}\n dep_times_station = {dep_times_station}, CUTOFF = {CUTOFF_EXPIRED_DESTINATIONS}")
                
        return DepArray
            
    def get_startstationindex_for_updateFunction(self,diva_meassure_station,line_meassured,line_direction):
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
        pass

        
    def departure_countdown_from_station(self,departures):
        L = []
        for departure in departures:
            dep_time_str = departure["departureTime"]["timePlanned"]
            dep_time = time.strptime(dep_time_str,'%Y-%m-%dT%H:%M:%S.000%z')
            dep_datetime = datetime.datetime.fromtimestamp(time.mktime(dep_time))
            
            delta_time = dep_datetime-self.Ref_Time
            L.append(delta_time.total_seconds())
        return np.array(L)
         


    

#string time in JSON-Response to datetime obj
def dateTimeFromString(string):
    String_Time = time.strptime(string,'%Y-%m-%dT%H:%M:%S.000%z')
    return datetime.datetime.fromtimestamp(time.mktime(String_Time))




