import numpy as np
import time
from datetime import datetime

from Depart import Departures

blink_half_period = 1 #seconds, time the led stays on and time led stays off in blinking mode
#GPIO
PINS_LINE_SELECT = {"U1":14,"U2":15,"U3":18,"U4":25,"U5":8,"U6":7}
PIN_SDO = 12
PIN_CLK = 16
PIN_OE_NOT = 20
PIN_LATCH = 21
SHIFT_REGISTER_SIZE = 48

class Monitor:
    def __init__(self,Lines) -> None:
        self.Lines = Lines
        self.init_display()
        self.ref_time = datetime.now()
    #------------GPIO-----------------------------------------------------------------------

    def init_display(self):
    #set all transistors off
    #output enable = high (no display)
    #latch = false
    #...
        return  


    def lightDisplay(self,De:Departures,ref_time:datetime):
        DisplayData = De.updateDisplayData()
        self.ref_time = ref_time
        for line in self.Lines:
            
            #myb a timefunction for controlling on time of leds
            LinePin = PINS_LINE_SELECT[line]
            #GPIO.output(LinePin,0) #set transistor on
            
            ### Transmit signal
            Number_of_stations = len(DisplayData[line])
            for i in range(SHIFT_REGISTER_SIZE-Number_of_stations+1): #padding #TODO check if the +1 is needed
                self.push_shiftregister(0)
            
            for i in range(Number_of_stations,1,-1): #reverse order
                self.push_shiftregister(DisplayData[line][i])
            
            #latch_data
            self.push_shiftregister(DisplayData[line][0],latch=True)
            
            ### light leds
            #GPIO.output(PIN_OE_NOT,0)
            time.sleep(0.02) # 
            #GPIO.output(PIN_OE_NOT,1)
            #GPIO.output(LinePin,1) #transistor off

    def push_shiftregister(self,led_state,latch = False):
        Led_turned_on = self.Led_state(led_state)
        #GPIO.output(PIN_SDO,int(Led_turned_on))
    #    if(latch):
            #GPIO.output(PIN_LATCH,1)
        #GPIO.output(PIN_CLK,1)
        #GPIO.output(PIN_CLK,0)
        #GPIO.output(PIN_LATCH,0)
        #GPIO.output(PIN_SDO,0)
        return

    def Led_state(self,led_state:int):
        if(led_state<=1):
            return led_state
        return (1 + self.seconds_since_ref_time()//blink_half_period) % 2
    
    def seconds_since_ref_time(self):
        return int((datetime.datetime.now()-self.ref_time).total_seconds())
