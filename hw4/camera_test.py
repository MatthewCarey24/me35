# This work is licensed under the MIT license.
# Copyright (c) 2013-2023 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE
#
# Edge detection with Canny:
#
# This example demonstrates the Canny edge detector.
import sensor
import image
import time
from mqtt import MQTTClient

sensor.reset()  # Initialize the camera sensor.
sensor.set_pixformat(sensor.GRAYSCALE)  # or sensor.RGB565
sensor.set_framesize(sensor.QQVGA)  # or sensor.QVGA (or others)
sensor.skip_frames(time=2000)  # Let new settings take affect.
sensor.set_gainceiling(8)

def callback(topic, msg):
    print((topic.decode(), msg.decode()))
    
mqtt_broker = 'broker.hivemq.com' 
port = 1883
topic_sub = 'ME35-24/cameraTest'       # this reads anything sent to ME35
topic_pub = 'ME35-24/cameraTest'

client = MQTTClient('ME35_chris', mqtt_broker , port, keepalive=60)
client.connect()
print('Connected to %s MQTT broker' % (mqtt_broker))
client.set_callback(callback)          # set the callback if anything is read
client.subscribe(topic_sub.encode())   # subscribe to a bunch of topics

msg = 'Hello World'


clock = time.clock()  # Tracks FPS.
while True:
    clock.tick()  # Track elapsed milliseconds between snapshots().
    img = sensor.snapshot()  # Take a picture and return the image.
    # Use Canny edge detector
    img.find_edges(image.EDGE_CANNY, threshold=(80, 100))
    # Faster simpler edge detection
    # img.find_edges(image.EDGE_SIMPLE, threshold=(100, 255))
    print(clock.fps())  # Note: Your OpenMV Cam runs about half as fast while
