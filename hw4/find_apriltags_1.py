# This work is licensed under the MIT license.
# Copyright (c) 2013-2023 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE
#
# AprilTags Example
#
# This example shows the power of the OpenMV Cam to detect April Tags
# on the OpenMV Cam M7. The M4 versions cannot detect April Tags.

import sensor
import time
import math
import network
from mqtt import MQTTClient

SSID = "Tufts_Robot"  # Network SSID
KEY = ""  # Network key
mqtt_broker = 'broker.hivemq.com'

# Init wlan module and connect to network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)

while not wlan.isconnected():
    print('Trying to connect to "{:s}"...'.format(SSID))
    time.sleep_ms(1000)

# We should have a valid IP now via DHCP
print("WiFi Connected ", wlan.ifconfig())

topic_pub = 'ME35-24/camera-test'

client = MQTTClient('ME35_openmv', mqtt_broker, port=1883, keepalive=60)
client.connect()
print('Connected to %s MQTT broker' % (mqtt_broker))


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  # must turn this off to prevent image washout...
sensor.set_auto_whitebal(False)  # must turn this off to prevent image washout...
clock = time.clock()

# Define camera calibration parameters.
# Adjust fx, fy, cx, cy according to your camera's calibration or lens characteristics.
fx = 160  # Focal length in pixels along the x-axis.
fy = 160  # Focal length in pixels along the y-axis.
cx = 80   # Principal point x (typically image width / 2).
cy = 60   # Principal point y (typically image height / 2).

# Main loop
while True:
    clock.tick()
    img = sensor.snapshot()

    # Add fx, fy, cx, and cy parameters in the find_apriltags() function call
    for tag in img.find_apriltags(fx=fx, fy=fy, cx=cx, cy=cy):
        img.draw_rectangle(tag.rect(), color=(255, 0, 0))
        img.draw_cross(tag.cx(), tag.cy(), color=(0, 255, 0))
        print_args = (tag.family(), tag.id(), (180 * tag.rotation()) / math.pi)
        msg = 'turn_right'
        print(msg)
        client.publish(topic_pub.encode(),msg.encode())

