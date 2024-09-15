import datetime
import numpy as np
import urllib.request,json
from Depart import Departures
import Depart

#global variables, designed to be constants
DISPLAY_MODE = 1 #int - 0 or 1, 0 for approximate live in station times, 1 for continous mode
DEBUG_MODE = 1 #if equals 1 then no live data is loaded, instead a file with some d
LINES = ["U1","U2","U3","U4","U6"]


TRAIN_IN_STATION_TIME = 30 #seconds ... time the light gets illuminated in a station by a train
TRAIN_DEPARTURE_DELAY_TIME_OFFSET = -15 #seconds ... time the light gets illuminated bevore the train is in station according to SET_OF_DEPARTURES

#Departure Data
STATIONS_MEASSURED = [["Landstraße","Westbahnhof","Praterstern"],
                      ["Leopoldau","Schottentor","Simmering"],
                      ["Heiligenstadt","Floridsdorf"],
                      ["Oberlaa","Seestadt","Ottakring"],
                      ["Hütteldorf","Siebenhirten"]]
DEPARTURE_LOOKAHEAD = 2 #how many departures
CUTOFF_EXPIRED_DEPARTURES = -30 #seconds, departures not in list when departure_time lower than this var

MIN_REFRESH_INTERVALL = 45 #seconds, checkforupdate will wait with updating data until this time intervall between updates is reached
MAX_REFRESH_INTERVALL = 180 #seconds

def seconds_since(since_time):
        return (datetime.datetime.now()-since_time).total_seconds()


class FetchData:
    def __init__(self,do_not_fetch= False) -> None:
        all_meassured_stations = [name for onelist in STATIONS_MEASSURED for name in onelist]
        self.De = Departures(LINES,all_meassured_stations)
        self.ref_time = np.zeros(len(STATIONS_MEASSURED),dtype=object)

        if(do_not_fetch): return

        if(DEBUG_MODE):#TODO add more files for debugging mode, add ref_time overwrite so that the data is actually usefull
            with open("WienerLinienMonitor\\python\\monitor.json",encoding="utf-8") as file:
                data = json.load(file)
            self.updateDepartures(data)
            debug_time = "2024-08-21T16:21:42.000+0200"
            self.ref_time[0] = Depart.dateTimeFromString(debug_time)
            return
        self.ref_time[0] = datetime.datetime.now()
        self.__fetch(STATIONS_MEASSURED[0])
        
        
        pass
    
    def __fetch(self,meassured_stations:list):
        """ input: meassured_stations - list of diva numbers of the stations to be meassured
            1. loads json response from API
            2. updates the Departure Object with the json data

        """
        
        #TODO add catch block for bad response, that waits 10sec and then tries one more time
        URL = self.generateAPI_URL(meassured_stations)
        with urllib.request.urlopen(URL) as url:
                data = json.loads(url.read().decode())
        self.updateDepartures(data)
    
    def check_for_updates(self):
        """ if the last update is no longer than MIN_REFRESH_INTERVALL seconds ago, no update is 
        performed if any element of STATIONS_MEASSURED has never been loaded it loads the first 
        of them otherwise it loads the element of STATIONS_MEASSURED that is the most outdated, 
        if the update was more then MAX_REFRESH_INTERVALL seconds ago
        """
        only_theupdated_ones = self.ref_time[self.ref_time!=0]
        last_updated_time = np.max(only_theupdated_ones)
        if(seconds_since(last_updated_time)<MIN_REFRESH_INTERVALL):
            return
        never_been_updated = np.where(self.ref_time==0)[0]
        if(any(never_been_updated)):
            updated_index = never_been_updated[0]
            self.ref_time[updated_index] = datetime.datetime.now()
            self.__fetch(STATIONS_MEASSURED[updated_index])
            return
        #it is now ensured that every element of ref_time is of type datetime
        longest_without_update = np.min(self.ref_time)
        if(seconds_since(longest_without_update)>MAX_REFRESH_INTERVALL):
            updated_index = np.argmin(self.ref_time)
            self.ref_time[updated_index] = datetime.datetime.now()
            self.__fetch(STATIONS_MEASSURED[updated_index])
            return
    
    def updateDepartures(self,data):
        Stops = data["data"]["monitors"]
        for Stop in Stops:
            stop_diva = int(Stop["locationStop"]["properties"]["name"])
            if(stop_diva in self.De.STATION_NAME_DICT):
                self.updateStop(stop_diva,Stop)

    def updateStop(self,stop_diva,Stop):
        for departing_line in Stop["lines"]:
            line = departing_line["name"]
            if(line in LINES):
                self.De.appendToDep(stop_diva,departing_line)

    def generateAPI_URL(self,station_name_List):
        assert len(station_name_List)>0
        start = "https://www.wienerlinien.at/ogd_realtime/monitor?diva="
        between = "&diva="
        string = start + str(self.De.getDiva(station_name_List[0].upper()))
        for name in station_name_List[1:]:
            string += between + str(self.De.getDiva(name.upper()))
        return string
    
    def getDisplayData(self):
        self.De.updateDisplayData()
        return self.De
    
    def getLINES(self):
        return LINES
    
     
 