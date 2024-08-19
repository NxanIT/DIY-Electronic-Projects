from livedata import LoadData
import livedata
import monitor
import turtle
from turtle import Turtle
import time
import numpy as np
import pandas as pd

LineDirectionCorrection = {'U1':True,'U2':True,'U3':False,'U4':True,'U6':True}

coordinates_pd = pd.read_csv("WienerLinienMonitor\\python\\Coordinates-demo.csv",sep=";")
Coordinates_of_line = {}
screen_width,screen_height = 1080,780
for line in livedata.LINES:
    L = []
    length = len(coordinates_pd["Text" + line])
    for index in range(length):
        L.append([[coordinates_pd[line + "x"][index],coordinates_pd[line + "y"][index]]])
    Coordinates_of_line[line] = np.array(L)

DemoDisplayData = {'U1': np.array([[1, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],
       [0, 0]]), 'U2': np.array([[1, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],
       [0, 0]]), 'U3': np.array([[0, 1],[0, 1],[0, 0],[0, 1],[0, 1],[0, 1],[0, 0],[0, 1],[0, 1],[0, 0],[1, 1],[1, 1],[0, 0],[0, 0],[1, 0],[1, 0],[0, 0],[0, 0],[0, 0],[0, 0],
       [0, 0]]), 'U4': np.array([[1, 0],[1, 0],[0, 0],[1, 0],[1, 0],[0, 0],[1, 0],[1, 0],[1, 0],[0, 0],[1, 0],[0, 0],[0, 0],[0, 1],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],
       [0, 0]]), 'U6': np.array([[1, 0],[1, 0],[1, 0],[1, 0],[1, 0],[1, 0],[1, 0],[1, 0],[1, 0],[1, 0],[0, 1],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],
       [0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0]])}

DemoDisplayData_2 = {}
for line in DemoDisplayData.keys():
    DemoDisplayData_2[line] = np.ones(np.shape(DemoDisplayData[line]))

def get_coordinates(line,index):
    return Coordinates_of_line[line][index][0]
    
def drawArrow(t:Turtle,coord,up=True,color="purple"):
    delta_coord = [5*(up==True),5*(up==True)] # up arrows will be shifted positive, down arrows negative that amount of pixels
    t.color(color)
    t.width(2)
    t.ht()
    t.penup()
    t.goto(coord[0] + delta_coord[0]-screen_width//2,-coord[1] - delta_coord[1]+screen_height//2)
    t.setheading(90 + 180*(up==False))
    t.pendown()
    t.forward(10)
    t.right(135)
    t.forward(5)
    t.right(135)
    t.forward(7)
    t.right(135)
    t.forward(7)
    t.penup()
    #t.st()
    #t.home()

def update_turtlet(t:Turtle,DisplayData):
    for line in DisplayData.keys():
        lineData = DisplayData[line]
        for i,j in np.ndindex(np.shape(lineData)):
            if(lineData[i,j] == 1): drawArrow(t,get_coordinates(line,i), up=(bool(j)!=LineDirectionCorrection[line]))
    pass

def demo():
    t = Turtle()
    screen = turtle.Screen()
    screen.setup(screen_width,screen_height)
    screen.bgpic("WienerLinienMonitor\\SVP-forpythondemo.png")
    DisplayData = DemoDisplayData_2
    #Data = LoadData()
    while(True):
        if(input("enter \"stop\" to exit")=="stop"):
            break
        #DisplayData = Data.updateDisplayData()
        #print(DisplayData)
        #update_turtle(t,DisplayData)
        t.clear()
        t.speed(0)
        update_turtlet(t,DisplayData)
        

if __name__=="__main__":
    demo()