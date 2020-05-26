#!/usr/bin/env python

import json
import unicornhat as unicorn
import threading
from time import sleep
from datetime import datetime
from gpiozero import CPUTemperature

from flask import Flask, jsonify, make_response, request
from random import randint

blinkThread = None
globalRed = 0
globalGreen = 0
globalBlue = 0
globalLastCalled = None
globalLastCalledApi = None

# setup the unicorn hat
unicorn.set_layout(unicorn.AUTO)
unicorn.brightness(0.5)

# get the width and height of the hardware
width, height = unicorn.get_shape()

app = Flask(__name__)


def setColor(r, g, b, brightness, speed):
    global crntColors, globalBlue, globalGreen, globalRed
    globalRed = r
    globalGreen = g
    globalBlue = b

    if brightness != '':
        unicorn.brightness(brightness)

    for y in range(height):
        for x in range(width):
            unicorn.set_pixel(x, y, r, g, b)
    unicorn.show()

    if speed != '':
        sleep(speed)
        unicorn.clear()
        crntT = threading.currentThread()
        while getattr(crntT, "do_run", True):
            for y in range(height):
                for x in range(width):
                    unicorn.set_pixel(x, y, r, g, b)
            unicorn.show()
            sleep(speed)
            unicorn.clear()
            unicorn.show()
            sleep(speed)


def switchOn():
    red = randint(10, 255)
    green = randint(10, 255)
    blue = randint(10, 255)
    blinkThread = threading.Thread(
        target=setColor, args=(red, green, blue, '', ''))
    blinkThread.do_run = True
    blinkThread.start()


def switchOff():
    global blinkThread, globalBlue, globalGreen, globalRed
    globalRed = 0
    globalGreen = 0
    globalBlue = 0
    if blinkThread is not None:
        blinkThread.do_run = False
    unicorn.clear()
    unicorn.off()


def setTimestamp():
    global globalLastCalled
    globalLastCalled = datetime.now()


# API Initialization
@app.route('/api/on', methods=['GET'])
def apiOn():
    global globalLastCalledApi
    globalLastCalledApi = '/api/on'
    switchOff()
    switchOn()
    setTimestamp()
    return jsonify({})


@app.route('/api/off', methods=['GET'])
def apiOff():
    global crntColors, globalLastCalledApi
    globalLastCalledApi = '/api/off'
    crntColors = None
    switchOff()
    setTimestamp()
    return jsonify({})


@app.route('/api/switch', methods=['POST'])
def apiSwitch():
    global blinkThread, globalLastCalledApi
    globalLastCalledApi = '/api/switch'
    switchOff()
    content = request.json
    red = content.get('red', '')
    green = content.get('green', '')
    blue = content.get('blue', '')
    brightness = content.get('brightness', '')
    speed = content.get('speed', '')
    blinkThread = threading.Thread(
        target=setColor, args=(red, green, blue, brightness, speed))
    blinkThread.do_run = True
    blinkThread.start()
    setTimestamp()
    return make_response(jsonify())


@app.route('/api/status', methods=['GET'])
def apiStatus():
    global globalBlue, globalGreen, globalRed
    global globalLastCalled, globalLastCalledApi
    cpu = CPUTemperature()
    return jsonify({
        'red': globalRed, 'green': globalGreen, 'blue': globalBlue,
        'lastCalled': globalLastCalled, 'cpuTemp': cpu.temperature,
        'lastCalledApi': globalLastCalledApi})


@app.route('/api/color/<color>', methods=['GET'])
def apiColor(color):
    global globalLastCalledApi
    globalLastCalledApi = '/api/color/' + color
    if color == 'red':
        blinkThread = threading.Thread(
          target=setColor, args=(255, 0, 0, 0.4, 0))
    if color == 'green':
        blinkThread = threading.Thread(
          target=setColor, args=(0, 255, 0, 0.4, 0))
    if color == 'yellow':
        blinkThread = threading.Thread(
          target=setColor, args=(255, 205, 0, 0.4, 0))
    blinkThread.do_run = True
    blinkThread.start()
    setTimestamp()
    return jsonify({})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)