from datetime import datetime

import Conversions
from Conversions import FetchData
from monitor import Monitor

LOOP_DEBUG_MODE = True

def main():
    time = datetime.now()
    Fe = FetchData()

    Mo = Monitor(Conversions.LINES)
    Mo.init_display()

    while(True):
        
        De = Fe.getDisplayData()
        print("took",(datetime.now()-time).total_seconds(),"seconds.")
        time = datetime.now() # TODO
        De.printDepartures()
        while(int(Conversions.seconds_since(time))<1):
            Mo.lightDisplay(De,time)
        Fe.check_for_updates()
        val = input("Debug mode, enter \"stop\" to exit.") if LOOP_DEBUG_MODE else ""
        if(val=="stop"): break
    pass

if(__name__=="__main__"):
    main()