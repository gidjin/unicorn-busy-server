# Simple server for Raspberry Pi with Pimoroni Unicorn hat

This is forked from https://github.com/estruyf/unicorn-busy-server and detailed instructions on the original setup is here.

https://www.eliostruyf.com/diy-building-busy-light-show-microsoft-teams-presence/

This fork extends the idea a little bit, adding some more functions to the server

## The busy light service
For the service, I wrote myself a straightforward API. At the moment it contains the following API endpoints:

| endpoint | request type | description |
| -------- | ------------ | ----------- |
| api/on | GET | turn the LEDs on, it will set a random color. |
| api/off | GET | think you can guess what it does. |
| api/status | GET | Returns the current RGB colors, timestamp of the last call, last called API, and the CPU temperature. |
| api/switch | POST | This allows you to specify the colors to set. The below request body is required |

### api/switch request body
```json
{
  "red": 0,
  "green": 0,
  "blue": 0,
  "brightness": 0.5,
  "speed": null
}
```

  * red, green, blue are values between `0-255`
  * brightness is 0.5 by default, you can specify between 0.4 and 1. This property is optional.
  * speed is optional and allows you to set the blinking speed in seconds. If you want to get more attention for your busy light.

## Setup

The quickest way to start is to get the files copied to your Raspberry Pi (if you want, you can install Git, which makes it easier to clone and fetch updates later). Once you copied the files, you should be able to run the install.sh script. This script installs the required Python dependencies.

Once all dependencies installed successfully, it is time to test out the API. You can execute the following script to get the API up and running: python3 server.py.

When the API is up and running, you can test out the API endpoints like api/on and api/off. If you verified the API works, you could create a start-up service. That way, each time you reboot the Raspberry Pi, it will automatically start. The steps I used for this are the following:

Copy the service file via: sudo cp busylight.service /etc/systemd/system/busylight.service.
Start the service sudo systemctl start busylight (to see if it is correctly copied and can start). If you want, you can use sudo systemctl status busylight to verify the status of the service.
Enable the service: sudo systemctl enable busylight.
That is all you need to do for the busy light API service.

## Install

## Service

```
sudo cp busylight.service /etc/systemd/system/busylight.service
```

Testing the service:

```
sudo systemctl start busylight.service
sudo systemctl stop busylight.service
sudo systemctl status busylight.service
```

Enable/disable for startup:

```
sudo systemctl enable busylight.service
sudo systemctl disable busylight.service
```