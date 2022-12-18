from mqttclient import MQTTClient
import network
import sys
import time
from machine import TouchPad, Pin, I2C, PWM
from binascii import hexlify


# Set up LSM6DSO
i2c = I2C(1,scl=Pin(22),sda=Pin(23),freq=400000)

for i in range(len(i2c.scan())):
	print(hex(i2c.scan()[i]))

# LSM6DSO functions
def WHOAMI(i2caddr):
	whoami = i2c.readfrom_mem(i2caddr,0x0F,1)
	return (hex(int.from_bytes(whoami,"little")))

def Temperature(i2caddr):
	temperature = i2c.readfrom_mem(i2caddr,0x20,2)
	if int.from_bytes(temperature,"little") > 32767:
		temperature = int.from_bytes(temperature,"little")-65536
	else:
		temperature = int.from_bytes(temperature,"little")
	return ((temperature)/(256) + 25)

def Zaccel(i2caddr):
	zacc = int.from_bytes(i2c.readfrom_mem(i2caddr,0x2C,2),"little")
	if zacc > 32767:
		zacc = zacc -65536
	return (zacc/16393)

def Xaccel(i2caddr):
	xacc = int.from_bytes(i2c.readfrom_mem(i2caddr,0x28,2),"little")
	if xacc > 32767:
		xacc = xacc -65536
	return (xacc/16393)

def Yaccel(i2caddr):
	yacc = int.from_bytes(i2c.readfrom_mem(i2caddr,0x2A,2),"little")
	if yacc > 32767:
		yacc = yacc -65536
	return (yacc/16393)


buff=[0xA0]
i2c.writeto_mem(i2c.scan()[i],0x10,bytes(buff))
i2c.writeto_mem(i2c.scan()[i],0x11,bytes(buff))
time.sleep(0.1)

# Capacitance sensing function
def cap() :
    t = TouchPad(Pin(14))
    return t.read()


# Check wifi connection
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
ip = wlan.ifconfig()[0]
if ip == '0.0.0.0':
    print("no wifi connection")
    sys.exit()
else:
    print("connected to WiFi at IP", ip)

# Set up Adafruit connection
adafruitIoUrl = 'io.adafruit.com'
adafruitUsername = 'gpimpale'
adafruitAioKey = 'aio_sdoo83HYPhkH6iqfGh4Mb6f1D5yW'

# Define callback function
def sub_cb(topic, msg):
    print((topic, msg))

# Connect to Adafruit server
print("Connecting to Adafruit")
mqtt = MQTTClient(adafruitIoUrl, port='1883', user=adafruitUsername, password=adafruitAioKey)
time.sleep(0.5)
print("Connected!")

# This will set the function sub_cb to be called when mqtt.check_msg() checks
# that there is a message pending
mqtt.set_callback(sub_cb)

# Set motor GPIO pins
gpio27 = Pin(27, Pin.OUT)
gpio15 = Pin(15, Pin.OUT)

cap_init = cap()
ERV = 2.4 #NOTE: This need sto be calibrated for each person 

# Main Loop
while True:
    # Cap
    feedName = "gpimpale/feeds/cap_feed"
    cap = cap()
    testMessage = str(cap)
    mqtt.publish(feedName, testMessage)
    print("Published {} to {}.".format(testMessage,feedName))

    # XYZ Accel
    feedName = "gpimpale/feeds/accel_feed"
    testMessage = str((Xaccel(i2c.scan()[i]), Yaccel(i2c.scan()[i]), Zaccel(i2c.scan()[i])))
    mqtt.publish(feedName, testMessage)
    print("Published {} to {}.".format(testMessage,feedName))

    # Calculate Volume
    d = 1/(1000 - cap)
    d_corr = d - 1/(1000 - cap_init)
    L = d_corr*(ERV/(1/(1000 - cap_init)))
    feedName = "gpimpale/feeds/lit_feed"
    testMessage = str(L)
    mqtt.publish(feedName, testMessage)
    print("Published {} to {}.".format(testMessage,feedName))

    # Set motor freq
    f = (10000*(Xaccel(i2c.scan()[i]))**2 + Yaccel(i2c.scan()[i])**2 + Zaccel(i2c.scan()[i])**2)
    # time.sleep(2) #TODO: NOTE, this is due to the limited data rate on Adafruit.io

    pwm = PWM(gpio15, freq=f, duty=50)
    pwm.init()
    time.sleep(2)
    pwm.deinit()
