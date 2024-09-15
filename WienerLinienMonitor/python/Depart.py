from datetime import datetime
import time
import numpy as np
import pandas as pd
import warnings

DEBUG_MODE = 1
debug_time = "2024-08-21T16:21:42.000+0200"

def dateTimeFromString(string):
    """Takes the formatet departure time string and returns a datetime object
    """
    String_Time = time.strptime(string,'%Y-%m-%dT%H:%M:%S.000%z')
    return datetime.fromtimestamp(time.mktime(String_Time))

DEBUG_TIME = dateTimeFromString(debug_time)

class Departures:
    def init_STATIONS(self):
        stations_pd = pd.read_csv("WienerLinienMonitor\\python\\Coordinates.csv",sep=";")
        def stations_of_line(line):
            stations_of_line = []
            for station_diva in stations_pd[line]:
                if(station_diva>0):
                    stations_of_line.append(int(station_diva))
            return stations_of_line
        
        for line in self.LINES:
            self.STATIONS[line] = np.array(stations_of_line(line))

    def init_STATION_NAME_DICT(self):
        stations_pd = pd.read_csv("WienerLinienMonitor\\python\\Coordinates.csv",sep=";")
        for line in self.LINES:
            for index in range(len(stations_pd[line])):
                diva = stations_pd[line].iloc[index]
                if diva>0: #diva is not nan
                    text = stations_pd["Text"+line].iloc[index]
                    self.STATION_NAME_DICT[int(diva)] = text.upper()

    def init_ALL_MEASSURED_INDICES(self,station_names:list):
        """important: STATION_NAME_DICT and STATIONS has to be defined for this function to work
        """
        for line in self.LINES:
            L = []
            for station_name in station_names:
                diva = self.getDiva(station_name)
                if(diva in self.STATIONS[line]):
                    L.append(self.getStationIndex(line,diva))
            L.sort()
            self.ALL_MEASSURED_IND[line] = np.array(L)
        self.init_STATION_DATA_RANGE()

    def init_STATION_DATA_RANGE(self):
        """computes the range of stations each meassured station takes effekt over
        """
        self.STATION_DATA_RANGE = {}
        for line in self.LINES:
            meassured = self.ALL_MEASSURED_IND[line]
            size = np.size(meassured)
            L_begin,L_end = meassured.copy(),meassured.copy()
            L_begin[1:] = (meassured[1:]+meassured[:size-1])//2
            L_end[:size-1] = L_begin[1:]-1
            self.STATION_DATA_RANGE[line] = np.array([L_begin,L_end]).T


    def __init__(self,Lines,All_meassured_stations:list) -> None:
        self.dep = {}
        self.__displaymode = 0 #default
        self.LINES = Lines
        self.STATION_NAME_DICT = {}
        self.STATIONS = {}#keys are DIVA numbers, val are Station Names
        self.ALL_MEASSURED_IND = {}
        self.init_STATIONS()
        self.init_STATION_NAME_DICT()
        self.init_ALL_MEASSURED_INDICES(All_meassured_stations)
        
        

#-------------------
    def getStationName(self,diva):
        return self.STATION_NAME_DICT[diva]
    
    def lenOfLine(self,line):
        return np.size(self.STATIONS[line])

    def getDiva(self,string:str):
        string = string.upper()
        if(string in self.STATION_NAME_DICT.values()):
            return self.__getStationDiva(string)
        new_str = string
        while(" " in string):
            new_str = new_str[:new_str.rfind(" ")]
            if(new_str in self.STATION_NAME_DICT.values()):
                warnings.warn(f"name {string} not in STATION_NAME_DICT, will use {new_str} as key instead")
                return self.__getStationDiva(new_str)
        raise KeyError(f"name {string} not in STATION_NAME_DICT")
    def __getStationDiva(self,string:str):
        index = list(self.STATION_NAME_DICT.values()).index(string)
        return int(list(self.STATION_NAME_DICT.keys())[index])
    def getStationIndex(self,line,station_diva):
        return np.where(self.STATIONS[line] == station_diva)[0][0]
    def stationNamefromIndex(self,line,index):
        return self.getStationName(self.STATIONS[line][index])

#-------------------
    def updateDisplaymode(self,displaymode):
        self.__displaymode = displaymode

    def appendToDep(self,station_diva:int,line_data:dict):
        line = line_data["name"]
        station_direction = line_data["direction"]
        #get first and last affected station index of line and direction traveling towards relative to own data computation
        meassured_index = self.getStationIndex(line,station_diva)
        assert(meassured_index in self.ALL_MEASSURED_IND[line])
        station_towards_name = str(line_data["towards"]).strip().upper()
        station_towards_diva = self.getDiva(station_towards_name)
        station_towards_index = self.getStationIndex(line,station_towards_diva)
        delta_index_positive = station_towards_index>=meassured_index
        traveling_index = int(delta_index_positive) #equals 1 if towards has a greater index in own data computation, else 0
        Meassured_spot = np.where(self.ALL_MEASSURED_IND[line] == meassured_index)[0][0]
        begin_index,end_index = self.STATION_DATA_RANGE[line][Meassured_spot]#TODO diffrent directions should range diffrently

        data = line_data["departures"]["departure"]
        L = []
        for train_data in data:
            if(not "departureTime" in train_data or not "vehicle" in train_data):
                warnings.warn(f"train departure data missing required argument(s). station is {self.getStationName(station_diva)}, towards: {station_towards_name}")
                continue
            departure_d = train_data["departureTime"]
            vehicle_d = train_data["vehicle"]
            planned_or_real = "timeReal" if "timeReal" in departure_d else "timePlanned"
            new_dep_time = dateTimeFromString(departure_d[planned_or_real])
            new_folding_ramp = "unknown"
            if("foldingRamp" in vehicle_d):
                new_folding_ramp = vehicle_d["foldingRamp"]
            else: print("foldingRamp not found")
            new_traffic_jam = vehicle_d["trafficjam"] 
            new_direction = vehicle_d["direction"]
            if(new_direction!=station_direction):
                warnings.warn(f"departing Train from {line}:{station_diva}-> {new_direction} does not match \
                              station_direction {station_direction}, this train is not beeing tracked")
                continue
            #TODO add option for new_direction not matching station_direction
            #create single dep obj
            single = Single_Departure(new_dep_time,new_folding_ramp,new_traffic_jam)
            #append single dep obj
            L.append(single)
            #TODO: ad breakpoint after enough departures has been loaded
        #if dep data has already entry at this station and line and direction, then check for some single departures if they are 
        # reasonably overlapping, if so then clip the old dep data out and put new data in
        old_L_both = [[],[]]
        if(not line in self.dep):
            old_L_both[station_direction=="H"] = L
            self.dep[line] = {meassured_index:old_L_both}
            return
        
        if(not meassured_index in self.dep[line]):
            old_L_both[station_direction=="H"] = L
            self.dep[line][meassured_index] = old_L_both
            return

        old_L_both = self.dep[line][meassured_index]
        old_L = old_L_both[station_direction=="H"]
        if(len(old_L)>0):
            L = self.concat_new_departures(line,meassured_index,station_direction,L)
        old_L_both[station_direction=="H"] = L
        pass
    
    
    def concat_new_departures(self,line:str,meassure_index:int,direction:str,new_List:list):
        MIN_OVERLAP = 3#TODO make this global
        TYP_CHECKLEN = 5
        DEV_ALLOWED = 1 # no. of traindep deviating from pattern allowed 

        old_list = self.dep[line][meassure_index][direction=="H"] #list
        old_len = len(old_list)
        for overlap in range(MIN_OVERLAP,old_len):
            start = old_len-overlap
            check_len = overlap if overlap<TYP_CHECKLEN else TYP_CHECKLEN
            L1 = old_list[start:start+check_len]
            L2 = new_List[:check_len]
            if(is_likely_the_same(L1,L2,DEV_ALLOWED)):
                concat_list = old_list[:start] + new_List
                return concat_list.sort()
        warnings.warn(f"concatenating departure data failed. No overlap \
                      between old and new departrures found.old={old_list}\\ new={new_List}")
        return (old_list+new_List).sort()

    def printDepartures(self):
        lengths = [self.lenOfLine(line) for line in self.LINES]
        max_len = max(lengths)
        print(type(self.dep),self.dep.keys())
        for line in self.dep.keys():
            data = self.dep[line]
            for key in data.keys():
                array = data[key]
                
                for dir in range(2):
                    print(f"{line} {self.stationNamefromIndex(line,key)[:5]:5s}",end=":")
                    for single in array[dir]:
                        dir_sym = ["\u2193","\u2191"]
                        print(f"{dir_sym[dir]} {single.totalseconds()}",end=" ")
                    print()
                print()
                    
        

    def updateDisplayData(self):
        D = {}
        for line in self.LINES:
            D[line] = self.__LineDisplayData(line)
        pass

    def __LineDisplayData(self,line):
        L = []
        for index in range(self.lenOfLine(line)):
            L.append(self.__StationDisplayData(line,index))
        return L
    
    def __StationDisplayData(self,line,index):
        DisplayFunctions = [self.__Displaymode0,self.__Displaymode1]
        LS = []
        for dir in range(2):
            LS.append(DisplayFunctions[self.__displaymode](line,index,dir))
        return LS
    
    def __Displaymode0(self,line,index,direction):#TODO
        pass

    def __Displaymode1(self,line,index,direction):#TODO
        pass


class LineDepartues:
    def __init__(self) -> None:
        pass

def datetime_diff(dt1:datetime,dt2:datetime):
    delta = dt2-dt1
    return abs(delta.total_seconds())

def is_likely_the_same(L1,L2,dev_allowed:list):
    length = min(len(L1),len(L2))
    deviations = 0
    for i in range(length):
        a,b = L1[i],L2[i]
        b_dep = b.get_dep()
        b_foldR = b.get_fold()
        b_tj = b.get_tj()
        if not a.could_be_same_train(b_dep,b_foldR,b_tj): deviations += 1
    return True if deviations <= dev_allowed else False

class Single_Departure:
    def __init__(self,dep_time:datetime,foldingRamp=True,trafficjam=False) -> None:
        self.dep_time = dep_time
        
        self.foldingRamp = foldingRamp
        self.trafficjam = trafficjam
        #TODO:check max delta time by studying deviations in live data
        self.SAME_TRAIN_MAX_DELTA_TIME = 60 + 10*datetime_diff(datetime.now(),dep_time)//60
    
    def get_dep(self):
        return self.dep_time
    def get_fold(self):
        return self.foldingRamp
    def get_tj(self):
        return self.trafficjam
    def totalseconds(self):
        if(DEBUG_MODE):
            return int((self.dep_time - DEBUG_TIME).total_seconds())
        return int((self.dep_time-datetime.now()).total_seconds())
    
    def could_be_same_train(self,other_dep_time:datetime,other_foldingRamp="unknown",other_trafficjam="unknown"):
        if(self.foldingRamp != other_foldingRamp and self.foldingRamp!="unknown" and other_foldingRamp !="unknown"):
            return False
        #TODO: is this needed??? should it return Nan???
        #if(other_trafficjam | self.trafficjam):
        #    return True
        
        if(datetime_diff(self.dep_time,other_dep_time)<self.SAME_TRAIN_MAX_DELTA_TIME):
            return True
    