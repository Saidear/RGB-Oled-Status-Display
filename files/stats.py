#!/usr/bin/python3
#-----------------------------------------------------------
#
#-----------------------------------------------------------

# Standard libraries
import time
#import math
import subprocess
from decimal import Decimal
from gpiozero import CPUTemperature
import os

# Graphics libraries
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# System Utilities
import psutil
import socket
#import vcgencmd


#Import Display
import RPi.GPIO as GPIO
import OLED_Driver as disp

# Initialize library.
#-------------OLED Init------------#
disp.Device_Init()



# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.SSD1351_WIDTH
height = disp.SSD1351_HEIGHT
image = Image.new("RGB", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = 0
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load Truetype font
font = ImageFont.truetype('cambriab.ttf',15)
font1 = ImageFont.truetype('cambriab.ttf',12)

#Fontawesome for Icons
font_icon = ImageFont.truetype('fa-solid-900.ttf', 10)
font3 = ImageFont.truetype('fa-solid-900.ttf', 11)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline= "BLACK" , fill="BLACK")

# Show Start Script text
draw.text((x, top), "Start Script",fill= "WHITE",font=font)
disp.Display_Image(image)

# Get Hostname
hostname = socket.gethostname()

# Gives a human-readable uptime string
def uptime():

     try:
         f = open( "/proc/uptime" )
         contents = f.read().split()
         f.close()
     except:
        return "Cannot open uptime file: /proc/uptime"

     total_seconds = float(contents[0])

     # Helper vars:
     MINUTE  = 60
     HOUR    = MINUTE * 60
     DAY     = HOUR * 24

     # Get the days, hours, etc:
     days    = int( total_seconds / DAY )
     hours   = int( ( total_seconds % DAY ) / HOUR )
     minutes = int( ( total_seconds % HOUR ) / MINUTE )
     seconds = int( total_seconds % MINUTE )

     # Build up the pretty string (like this: "N days, N hours, N minutes, N seconds")
     string = ""
     if days > 0:
         string += str(days) + (days == 1 and "d" or "d" ) + ", "
     if len(string) > 0 or hours > 0:
         string += str(hours) + (hours == 1 and "h" or "h" ) + ", "
     if len(string) > 0 or minutes > 0:
         string += str(minutes) + (minutes == 1 and "m" or "m" ) + ", "
     string += str(seconds) + (seconds == 1 and "s" or "s" )

     return string;

# No idea if this is needed or not, it's left over from the original file
mode=0

# Is WiFi or Ethernet active?  (prioritizes Ethernet)
def stat_icon():
    root= '/sys/class/net'
    netfaces = [ item for item in os.listdir(root) if os.path.isdir(os.path.join(root, item)) ]
    for x,val in enumerate(netfaces):
        os.chdir(root)
        os.chdir(val)
        f = open("operstate",'rt')
        status = f.read(2)
        f.close()
        if str(status) == "up":
            if 'eth' in val:
                status = 63382
            elif 'wlan' in val:
                status = 61931
            break
    return status;
counter_a = 0
counter_b = 0
while True:
    icon = 0
    if mode==0:
        if counter_a == 0: #what must run at start and execute every 60s
            cmd = "hostname -I | cut -d\' \' -f1"
            IP = subprocess.check_output(cmd, shell = True ) #IP address
            cmd = "df -h | awk '$NF==\"/\"{printf \"%d/%d GB\", $3,$2}'" # Disk Usage
            Disk = subprocess.check_output(cmd, shell = True )
        elif counter_a ==59:
            counter_a = 0
        else:
            counter_a +=1
        if counter_b == 0:  # what do we execute every 30s
            icon = stat_icon() # check internet connection after 30s
            cmd = "free -m | awk 'NR==2{printf \"%s/%s MB\", $3,$2 }'"
            MemUsage = subprocess.check_output(cmd, shell = True )
        elif counter_b == 29:
            counter_b = 0
        else:
            counter_b +=1
        # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    #Get CPU temp, format it
    cpu_raw = CPUTemperature()
    cpu = "%.1f" % cpu_raw.temperature

    #Colour system data if CPU is overload, or CPU temp risk throttling.
    if Decimal(cpu) < 60 and Decimal(cpu) > 10:
         colour = "GREEN"
    elif Decimal(cpu) < 75 and Decimal(cpu) > 59:
         colour = "YELLOW"
    else:
         colour = "RED"
         cpu = "%.0f" % cpu_raw.temperature

    # Get CPU frequency
    freq = int(psutil.cpu_freq().current)

    # Change format/colour based on CPU speed (Mhz/ Ghz)
    if freq > 999:
        freq = freq/1000
        freq="%.1f" % freq
        freq = str(freq) + str(" Ghz")
    else:
        freq = str(freq) + str(' Mhz')

    # Get CPU Usage, format if risk of throttling
    cpu_usage = psutil.cpu_percent()
    cpu_usage = "%.1f" % Decimal(cpu_usage)

    if Decimal(cpu_usage) < 50:
         colour2 = "GREEN"
    elif Decimal(cpu_usage) < 80 and Decimal(cpu_usage) > 49:
         colour2 = "YELLOW"
    else:
         colour2= "RED"
         cpu_usage = "%.0f" % cpu_usage


    # Set Lines for easy updating of icon/text associated with it.
    y = x+15
    wifi_line = top+25
    freq_line = top+40
    temp_line = top+55
    mem_line =  top+70
    disk_line = top+85

    #Draw Icons
    draw.text((x, wifi_line), chr(stat_icon()),  font=font_icon, fill="WHITE")
    draw.text((x, freq_line), chr(62171) ,  font=font3, fill="WHITE")
    draw.text((x+72, freq_line), chr(61952) ,  font=font_icon, fill="WHITE")
    draw.text((x+3, temp_line),  chr(62152),  font=font3, fill="WHITE")
    draw.text((x, mem_line), chr(62776),  font=font_icon, fill="WHITE")
    draw.text((x+2, disk_line), chr(61888),  font=font3, fill="WHITE")


    # Draw system stats
    draw.text((x, top),hostname, fill = "GREY", font = font)
    draw.text((y, wifi_line-4),       str(IP.decode('UTF-8')),  font=font1, fill=255)
    draw.text((y, freq_line-3), freq ,  font=font1, fill="White")
    draw.text((y+70, freq_line-3), cpu_usage + "%", font=font1, fill= colour2)
    draw.text((y, temp_line-3), cpu + u"\N{DEGREE SIGN}C", fill = colour,font = font1)
    draw.text((y, mem_line-3),    str(MemUsage.decode('UTF-8')), font=font1, fill="BLUE")
    draw.text((y, disk_line-3),    str(Disk.decode('UTF-8')),font=font1, fill="BLUE")
    draw.text((x, bottom-13),    str(uptime()),font=font1, fill= "WHITE")

    # Display image.
    disp.Display_Image(image)
    disp.Delay(900)
