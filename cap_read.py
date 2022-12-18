from machine import Pin
from machine import TouchPad, Pin

#import datetime as dt
#import matplotlib.pyplot as plt
#import matplotlib.animation as animation

# Ten capacitive touch-enabled (GPIO) pins on the ESP32: 
# 0, 2, 4, 12, 13 14, 15, 27, 32, 33

def cap() :
    t = TouchPad(Pin(14))
    return t.read()

def get_raw_cap():
    while True:
        print(str(cap()))