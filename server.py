#!/usr/bin/env python

import json

import os
import threading
import math
import colorsys
from time import sleep
from datetime import datetime
try:
	from gpiozero import CPUTemperature
	GPIOZERO_AVAILABLE = True
except ImportError:
	GPIOZERO_AVAILABLE = False
	print("gpiozero not available. CPU temperature will be mocked.")
from lib.unicorn_wrapper import UnicornWrapper
from flask import Flask, jsonify, make_response, request, send_from_directory
from flask_cors import CORS
from random import randint
from jsmin import jsmin
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Load webhook URLs from environment variables
WEBHOOK_AVAILABLE = os.getenv('WEBHOOK_AVAILABLE', '')
WEBHOOK_BUSY = os.getenv('WEBHOOK_BUSY', '')
WEBHOOK_AWAY = os.getenv('WEBHOOK_AWAY', '')
WEBHOOK_OFF = os.getenv('WEBHOOK_OFF', '')
WEBHOOK_RAINBOW = os.getenv('WEBHOOK_RAINBOW', '')

# Load startup mode from environment variable (default: RAINBOW)
STARTUP_MODE = os.getenv('STARTUP_MODE', 'RAINBOW').upper()

# Load port from environment variable (default: 5000)
PORT = int(os.getenv('PORT', '5000'))

blinkThread = None
crntColors = None
globalRed = 0
globalGreen = 0
globalBlue = 0
globalBrightness = 0
globalLastCalled = None
globalLastCalledApi = None
globalStatus = None
globalStatusOverwrite = False

# Initialize the Unicorn hat
unicorn = UnicornWrapper()

# get the width and height of the hardware and set it to portrait if its not
width, height = unicorn.getShape()


def call_webhook(webhook_url, status):
	"""
	Call webhook asynchronously with a simple GET request.
	Runs in a separate thread to avoid blocking the main request.
	"""
	if not webhook_url:
		return

	def _make_request():
		try:
			response = requests.get(webhook_url, timeout=5)
			print(f"Webhook called for {status}: {response.status_code}")
		except requests.exceptions.Timeout:
			print(f"Webhook timeout for {status}: {webhook_url}")
		except requests.exceptions.RequestException as e:
			print(f"Webhook error for {status}: {str(e)}")
		except Exception as e:
			print(f"Unexpected webhook error for {status}: {str(e)}")

	# Run webhook call in a separate thread (non-blocking)
	webhook_thread = threading.Thread(target=_make_request)
	webhook_thread.daemon = True
	webhook_thread.start()


class MyFlaskApp(Flask):
	def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
		if not self.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
			with self.app_context():
				startupRainbow()
		super(MyFlaskApp, self).run(host=host, port=port, debug=debug, load_dotenv=load_dotenv, **options)


app = MyFlaskApp(__name__, static_folder='frontend/build', static_url_path='/')
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


def setColor(r, g, b, brightness=0.5, speed=None):
	global crntColors
	setPixels(r, g, b, brightness)
	unicorn.show()

	if speed is not None and speed != '':
		crntT = threading.currentThread()
		unicorn.clear()
		while getattr(crntT, "do_run", True):
			setPixels(r, g, b, brightness)
			unicorn.show()
			sleep(speed)
			unicorn.clear()
			unicorn.show()
			sleep(speed)


def setPixels(r, g, b, brightness=0.5):
	global globalBrightness, globalBlue, globalGreen, globalRed

	globalRed = r
	globalGreen = g
	globalBlue = b

	if brightness is not None:
		globalBrightness = brightness
		unicorn.setBrightness(brightness)

	unicorn.setColour(r, g, b)


def switchOn():
	rgb = unicorn.hsvIntToRGB(randint(0, 360), 100, 100)
	blinkThread = threading.Thread(target=setColor, args=(rgb[0], rgb[1], rgb[2]))
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


def halfBlink():
	unicorn.show()
	sleep(0.8)
	unicorn.clear()
	unicorn.show()
	sleep(0.2)


def countDown(time):
	showTime = time - 12
	brightness = 0.5
	while showTime > 0:
		b = brightness
		for x in range(4):
			b = b - x
			setPixels(255, 255, 0, b)
			unicorn.show()
			sleep(0.5)
			unicorn.clear()
		unicorn.show()
		sleep(2)
		showTime = showTime - 2
	for i in range(10):
		setPixels(255, 0, 0, 0.5)
		halfBlink()
	setColor(255, 0, 0, 0.5)
	halfBlink()
	unicorn.clear()
	unicorn.off()


def displayRainbow(brightness, speed, run=None):
	global crntColors
	if speed is None:
		speed = 0.01
	if brightness is None:
		brightness = 0.5
	crntT = threading.currentThread()
	i = 0.0
	offset = 30
	while getattr(crntT, "do_run", True):
		i = i + 0.3
		unicorn.setBrightness(brightness)
		for x in range(0, width):
			for y in range(0, height):
				r = 0  # x * 32
				g = 0  # y * 32
				xy = x + y / 4
				r = (math.cos((x + i) / 2.0) + math.cos((y + i) / 2.0)) * 64.0 + 128.0
				g = (math.sin((x + i) / 1.5) + math.sin((y + i) / 2.0)) * 64.0 + 128.0
				b = (math.sin((x + i) / 2.0) + math.cos((y + i) / 1.5)) * 64.0 + 128.0
				r = max(0, min(255, r + offset))
				g = max(0, min(255, g + offset))
				b = max(0, min(255, b + offset))
				unicorn.setPixel(x, y, int(r), int(g), int(b))

		unicorn.show()
		sleep(speed)


def setTimestamp():
	global globalLastCalled
	globalLastCalled = datetime.now()


# API Initialization
@app.route('/', methods=['GET'])
def root():
	print(app.static_folder)
	return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/on', methods=['GET', 'POST'])
def apiOn():
	global globalStatusOverwrite, globalStatus, globalLastCalledApi
	globalStatusOverwrite = False
	globalStatus = 'on'
	globalLastCalledApi = '/api/on'
	switchOff()
	switchOn()
	setTimestamp()
	return make_response(jsonify({}))


@app.route('/api/off', methods=['GET', 'POST'])
def apiOff():
	global crntColors, globalStatusOverwrite, globalStatus, globalLastCalledApi
	globalStatusOverwrite = False
	globalStatus = 'off'
	globalLastCalledApi = '/api/off'
	crntColors = None
	switchOff()
	setTimestamp()
	call_webhook(WEBHOOK_OFF, 'Off')
	return make_response(jsonify({}))


@app.route('/api/switch', methods=['POST'])
def apiSwitch():
	global blinkThread, globalStatusOverwrite, globalStatus, globalLastCalledApi

	if globalStatusOverwrite:
		return make_response(jsonify({}))

	globalLastCalledApi = '/api/switch'
	switchOff()
	content = json.loads(jsmin(request.get_data(as_text=True)))
	red = content.get('red', None)
	green = content.get('green', None)
	blue = content.get('blue', None)
	if red is None or green is None or blue is None:
		return make_response(jsonify({'error': 'red, green and blue must be present and can\' be empty'}), 500)

	if red == 0 and green == 144 and blue == 0:
		globalStatus = 'Available'
	elif red == 255 and green == 191 and blue == 0:
		globalStatus = 'Away'
	elif red == 179 and green == 0 and blue == 0:
		globalStatus = 'Busy'
	else:
		globalStatus = None

	brightness = content.get('brightness', None)
	speed = content.get('speed', None)
	blinkThread = threading.Thread(target=setColor, args=(red, green, blue, brightness, speed))
	blinkThread.do_run = True
	blinkThread.start()
	setTimestamp()
	return make_response(jsonify())

@app.route('/api/available', methods=['GET', 'POST'])
def availableCall():
	global globalStatusOverwrite, globalStatus, globalLastCalledApi, blinkThread
	globalStatusOverwrite = True
	globalStatus = 'Available'
	globalLastCalledApi = '/api/available'
	switchOff()
	blinkThread = threading.Thread(target=setColor, args=(0, 144, 0))
	blinkThread.do_run = True
	blinkThread.start()
	setTimestamp()
	call_webhook(WEBHOOK_AVAILABLE, 'Available')
	return make_response(jsonify())

@app.route('/api/busy', methods=['GET', 'POST'])
def busyCall():
	global globalStatusOverwrite, globalStatus, globalLastCalledApi, blinkThread
	globalStatusOverwrite = True
	globalStatus = 'Busy'
	globalLastCalledApi = '/api/busy'
	switchOff()
	blinkThread = threading.Thread(target=setColor, args=(179, 0, 0))
	blinkThread.do_run = True
	blinkThread.start()
	setTimestamp()
	call_webhook(WEBHOOK_BUSY, 'Busy')
	return make_response(jsonify())

@app.route('/api/away', methods=['GET', 'POST'])
def awayCall():
	global globalStatusOverwrite, globalStatus, globalLastCalledApi, blinkThread
	globalStatusOverwrite = True
	globalStatus = 'Away'
	globalLastCalledApi = '/api/away'
	switchOff()
	blinkThread = threading.Thread(target=setColor, args=(255, 191, 0))
	blinkThread.do_run = True
	blinkThread.start()
	setTimestamp()
	call_webhook(WEBHOOK_AWAY, 'Away')
	return make_response(jsonify())

@app.route('/api/reset', methods=['GET', 'POST'])
def resetCall():
	global globalStatusOverwrite, globalStatus, globalLastCalledApi, blinkThread
	globalStatusOverwrite = False
	return make_response(jsonify())


@app.route('/api/rainbow', methods=['GET', 'POST'])
def apiDisplayRainbow():
	global blinkThread, globalStatus, globalLastCalledApi
	globalStatus = 'rainbow'
	globalLastCalledApi = '/api/rainbow'
	switchOff()

	# Default values
	brightness = None
	speed = None

	# Try to parse JSON if provided
	data = request.get_data(as_text=True)
	if data:
		try:
			content = json.loads(jsmin(data))
			brightness = content.get('brightness', None)
			speed = content.get('speed', None)
		except (json.JSONDecodeError, ValueError):
			pass  # Use defaults if JSON parsing fails

	blinkThread = threading.Thread(target=displayRainbow, args=(brightness, speed, None))
	blinkThread.do_run = True
	blinkThread.start()
	setTimestamp()
	if brightness is None:
		brightness = 0.5
	call_webhook(WEBHOOK_RAINBOW, 'Rainbow')
	return make_response(jsonify())


@app.route('/api/status', methods=['GET'])
def apiStatus():
	global globalStatusOverwrite, globalStatus, globalBlue, globalGreen, globalRed, globalBrightness, \
		globalLastCalled, globalLastCalledApi, width, height, unicorn

	if GPIOZERO_AVAILABLE:
		cpu = CPUTemperature()
		cpu_temp = cpu.temperature
	else:
		cpu_temp = 42.0  # Mock temperature for testing

	return jsonify({
		'red': globalRed,
		'green': globalGreen,
		'blue': globalBlue,
		'brightness': globalBrightness,
		'lastCalled': globalLastCalled,
		'cpuTemp': cpu_temp,
		'lastCalledApi': globalLastCalledApi,
		'height': height,
		'width': width,
		'unicorn': unicorn.getType(),
		'status': globalStatus,
		'statusOverwritten': globalStatusOverwrite
	})


@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)


def startupRainbow():
	"""Initialize the display based on STARTUP_MODE environment variable"""
	global blinkThread, globalStatus, globalStatusOverwrite

	startup_mode = STARTUP_MODE
	print(f"Starting up in {startup_mode} mode")

	if startup_mode == 'OFF':
		globalStatus = 'off'
		switchOff()
	elif startup_mode == 'AVAILABLE':
		globalStatusOverwrite = True
		globalStatus = 'Available'
		blinkThread = threading.Thread(target=setColor, args=(0, 144, 0))
		blinkThread.do_run = True
		blinkThread.start()
	elif startup_mode == 'BUSY':
		globalStatusOverwrite = True
		globalStatus = 'Busy'
		blinkThread = threading.Thread(target=setColor, args=(179, 0, 0))
		blinkThread.do_run = True
		blinkThread.start()
	elif startup_mode == 'AWAY':
		globalStatusOverwrite = True
		globalStatus = 'Away'
		blinkThread = threading.Thread(target=setColor, args=(255, 191, 0))
		blinkThread.do_run = True
		blinkThread.start()
	else:  # Default to RAINBOW
		globalStatus = 'rainbow'
		blinkThread = threading.Thread(target=displayRainbow, args=(1, 0.1, 1))
		blinkThread.do_run = True
		blinkThread.start()


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=PORT, debug=False)
