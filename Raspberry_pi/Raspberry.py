#!/usr/bin/python
# --------------------------------------
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#  lcd_i2c.py
#  LCD test script using I2C backpack.
#  Supports 16x2 and 20x4 screens.
#
# Author : Matt Hawkins
# Date   : 20/09/2015
#
# http://www.raspberrypi-spy.co.uk/
#
# Copyright 2015 Matt Hawkins
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------
import smbus
import time
import Adafruit_DHT

import datetime
import requests
import json

import RPi.GPIO as GPIO

import os

# Define some device parameters
I2C_ADDR = 0x27  # I2C device address
LCD_WIDTH = 16  # Maximum characters per line

# Define some device constants
LCD_CHR = 1  # Mode - Sending data
LCD_CMD = 0  # Mode - Sending command

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94  # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4  # LCD RAM address for the 4th line

LCD_BACKLIGHT = 0x08  # On
# LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100  # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

# Open I2C interface
# bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1


def lcd_init():
    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)


def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = the data
    # mode = 1 for data
    #        0 for command

    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

    # High bits
    bus.write_byte(I2C_ADDR, bits_high)
    lcd_toggle_enable(bits_high)

    # Low bits
    bus.write_byte(I2C_ADDR, bits_low)
    lcd_toggle_enable(bits_low)


def lcd_toggle_enable(bits):
    # Toggle enable
    time.sleep(E_DELAY)
    bus.write_byte(I2C_ADDR, (bits | ENABLE))
    time.sleep(E_PULSE)
    bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
    time.sleep(E_DELAY)


def lcd_string(message, line):
    # Send string to display

    message = message.ljust(LCD_WIDTH, " ")

    lcd_byte(line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)


DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4


def main():
    lcd_init()

    interval = 5
    count = 0

    temp_list = []
    hum_list = []

    serial = 4090

    target_temp = 0
    target_hum = 0
    pTarget_temp = 0
    pTarget_hum = 0

    temp_move = 0
    hum_move = 0

    own = 0
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(12, GPIO.OUT)
    GPIO.setup(18, GPIO.OUT)
    GPIO.setup(26, GPIO.OUT)

    GPIO.output(12, True)
    GPIO.output(18, True)
    GPIO.output(26, True)

    status = 22
    change = 0

    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if humidity is not None and temperature is not None:
            print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
        else:
            print("Failed to retrieve data from humidity sensor")
        temp = round(temperature, 2)
        hum = round(humidity, 2)

        temp_list.append(temp)
        hum_list.append(hum)

        temp_text = "TEMP = " + str(temp)
        hum_text = "HUM = " + str(hum)

        res = os.popen('sudo ifconfig eth1 | grep ether').readline()
        mac = res.lstrip().split(' ')[1]
        print(mac)

        if own is 0:
            GPIO.output(12, True)
            GPIO.output(18, True)
            GPIO.output(26, True)
            lcd_string(temp_text, LCD_LINE_1)
            lcd_string(hum_text, LCD_LINE_2)
            time.sleep(1)
            lcd_string(str(mac), LCD_LINE_1)
            lcd_string(str(serial), LCD_LINE_2)
            status = 22
            temp_move = 0
            hum_move = 0

        else:
            lcd_string(temp_text, LCD_LINE_1)
            lcd_string(hum_text, LCD_LINE_2)
            time.sleep(1)

        count = count + 1

        if own is 1:
            if target_temp > temp + 2:
                # temp up relay 12 light bulb
                GPIO.output(12, False)
                status = 30
                temp_move = 1
            elif target_temp < temp - 2:
                # temp down relay 18 fan
                GPIO.output(18, False)
                status = 10
                temp_move = -1
            elif target_temp + 1 > temp and target_temp - 1 < temp:
                # stop
                if hum_move == -1:
                    GPIO.output(18, True)
                else:
                    GPIO.output(12, True)
                    GPIO.output(18, True)
                status = 20
                temp_move = 0
            else:
                if temp_move == 0:
                    status = 20
                else:
                    if target_temp > temp:
                        status = 30
                    else:
                        status = 10

            if target_hum > hum + 8:
                # hum up relay 26 moisture
                GPIO.output(26, False)
                status = status + 3
                hum_move = 1
            elif target_hum < hum - 8:
                # hum down relay 12 light bulb
                GPIO.output(12, False)
                status = status + 1
                hum_move = -1
            elif target_hum + 3 > hum and target_hum - 3 < hum:
                # stop
                hum_move = 0
                if temp_move == 1:
                    GPIO.output(26, True)
                    status = status + 2
                else:
                    GPIO.output(12, True)
                    GPIO.output(26, True)
                    status = status + 2
            else:
                if hum_move == 0:
                    status = status + 2
                else:
                    if target_hum > hum:
                        status = status + 3
                    else:
                        status = status + 1
        print("status: ")
        print(status)
        print("temp_move: ")
        print(temp_move)
        print("hum_move: ")
        print(hum_move)

        if interval is count:
            count = 0

            tm = datetime.datetime.now()
            dt = tm.strftime('%Y-%m-%d %H:%M:%S.%f')
            data = {
                "temp_max": max(temp_list),
                "temp_min": min(temp_list),
                "temp_avg": round(sum(temp_list) / interval, 3),
                "hum_max": max(hum_list),
                "hum_min": min(hum_list),
                "hum_avg": round(sum(hum_list) / interval, 3),
                "cur_time": str(dt[:-7]),
                "serial": serial,
                "status": status,
                "mac": mac
            }
            json_data = json.dumps(data)
            r = requests.post('http://ec2-52-78-37-156.ap-northeast-2.compute.amazonaws.com:8000/sensing',
                              json=json_data)
            # r = requests.post('http://192.168.0.17:8000/sensing', json=json_data)
            # r = requests.post('http://121.175.166.188:8000/sensing', json=json_data)

            print(r.text)
            json_data = json.loads(r.text)

            target_temp = float(json_data["temp"])
            target_hum = float(json_data["hum"])

            if pTarget_temp == target_temp and pTarget_hum == target_hum:
                change = 0
            else:
                change = 1
            print(change)

            if change == 1:
                GPIO.output(12, True)
                GPIO.output(18, True)
                GPIO.output(26, True)
                status = 22
                temp_move = 0
                hum_move = 0

            pTarget_temp = target_temp
            pTarget_hum = target_hum
            own = json_data["connect"]

            print(target_temp)
            print(target_hum)
            print(own)
            temp_list = []
            hum_list = []


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        lcd_byte(0x01, LCD_CMD)