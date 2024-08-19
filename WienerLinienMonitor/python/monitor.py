import numpy as np
import time

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
    #------------GPIO-----------------------------------------------------------------------

    def init_display(self):
    #set all transistors off
    #output enable = high (no display)
    #latch = false
    #...
        return  


    def lightDisplay(self,DisplayData):
        for line in self.Lines:
            
            #myb a timefunction for controlling on time of leds
            LinePin = PINS_LINE_SELECT[line]
            #GPIO.output(LinePin,0) #set transistor on
            
            ### Transmit signal
            Number_of_stations = len(DisplayData[line])
            for i in range(SHIFT_REGISTER_SIZE): #padding
                self.push_shiftregister(0)
            
            for i in range(1,Number_of_stations,-1): #reverse order
                self.push_shiftregister(DisplayData[line][i])
            
            #latch_data
            self.push_shiftregister(DisplayData[line][0],latch=True)
            
            ### light leds
            #GPIO.output(PIN_OE_NOT,0)
            time.sleep(0.02) # 
            #GPIO.output(PIN_OE_NOT,1)
            #GPIO.output(LinePin,1) #transistor off

    def push_shiftregister(Led_turned_on,latch = False):
        #GPIO.output(PIN_SDO,int(Led_turned_on))
    #    if(latch):
            #GPIO.output(PIN_LATCH,1)
        #GPIO.output(PIN_CLK,1)
        #GPIO.output(PIN_CLK,0)
        #GPIO.output(PIN_LATCH,0)
        #GPIO.output(PIN_SDO,0)
        return
