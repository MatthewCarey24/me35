from machine import Pin, PWM, I2C
import neopixel
import uasyncio as asyncio
from mqtt import MQTTClient
import struct
import gc

# MQTT Settings
mqtt_broker = 'broker.hivemq.com'
topic_sub = 'ME35-24/startstop'

run_program = False
light_on = False
current_color_value = 0

# Accelerometer Class
class Acceleration():
    def __init__(self, scl, sda, addr=0x62):
        self.addr = addr
        self.i2c = I2C(1, scl=scl, sda=sda, freq=100000)
        self.connected = False
        if self.is_connected():
            print('Accelerometer connected')
            self.write_byte(0x11, 2)  # Start data stream

    def is_connected(self):
        options = self.i2c.scan()
        print("I2C devices found:", options)
        self.connected = self.addr in options
        return self.connected

    def read_accel(self):
        buffer = self.i2c.readfrom_mem(self.addr, 0x02, 6)  # Read 6 bytes
        return struct.unpack('<hhh', buffer)

    def write_byte(self, cmd, value):
        self.i2c.writeto_mem(self.addr, cmd, value.to_bytes(1, 'little'))

# Initialize Accelerometer
scl = Pin(27, Pin.OUT)
sda = Pin(26, Pin.OUT)
accelerometer = Acceleration(scl, sda)

def callback(topic, msg):
    global run_program
    global light_on
    msg_decoded = msg.decode()
    
    if msg_decoded == 'start':
        run_program = True
        print("Program started via MQTT.")
    elif msg_decoded == 'stop':
        run_program = False
        print("Program stopped via MQTT.")
    elif msg_decoded == 'on':
        light_on = True
        print("Light turned on via MQTT.")
    elif msg_decoded == 'off':
        light_on = False
        print("Light turned off via MQTT.")

# ---------------------------------Breathing-----------------------------
async def breathe():  
    light = PWM(Pin(0, Pin.OUT))
    light.freq(50)

    while True:
        if run_program:
            for i in range(0, 65535, 500):
                light.duty_u16(i)
                await asyncio.sleep(0.01)
            for i in range(65535, -1, -500):
                light.duty_u16(i)
                await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(0.1)  

# ---------------------------------LED/Button Toggle-----------------------------
async def toggle_light():
    global light_on
    button = Pin(20, Pin.IN, Pin.PULL_UP)  # Button with pull-up resistor
    led = neopixel.NeoPixel(Pin(28), 1)  # NeoPixel LED control on pin 28

    pressed_color = (10, 0, 10)
    resting_color = (0, 0, 0)
    
    button_pressed = False
    last_button_state = button.value()

    while True:
        if run_program:
            current_button_state = button.value()
            if last_button_state == 1 and current_button_state == 0:  # Button pressed
                light_on = not light_on
                if light_on:
                    led[0] = pressed_color
                    led.write()
                    print("LED turned on.")
                else:
                    led[0] = resting_color
                    led.write()
                    print("LED turned off.")
                await asyncio.sleep(0.5)  # Debounce delay
            last_button_state = current_button_state
        
        await asyncio.sleep(0.01)

# ---------------------------------Accelerometer Tap Detection-----------------------------
async def detect_tap():
    global light_on
    global current_color_value
    led = neopixel.NeoPixel(Pin(28), 1)  # NeoPixel LED control on pin 28
    tap_threshold = 2000  # Adjust as needed
    color_increment = 10  # Adjust as needed for the rate of color change
    stable_count = 0
    stable_threshold = 50  # Number of stable readings to confirm no tap

    last_magnitude = 0

    while True:
        if run_program and light_on:
            x, y, z = accelerometer.read_accel()
            # Calculate magnitude
            magnitude = (x**2 + y**2 + z**2)**0.5
            
            if magnitude > tap_threshold and last_magnitude <= tap_threshold:
                # Update the current color value and wrap around if needed
                current_color_value = (current_color_value + color_increment) % 256
                led[0] = (current_color_value, 0, 255 - current_color_value)  # Example color logic
                led.write()
                print("LED color changed to:", led[0])
                await asyncio.sleep(0.5)  # Debounce delay
            
            last_magnitude = magnitude
            
        await asyncio.sleep(0.01)


# ---------------------------------MQTT-----------------------------
async def mqtt_client():
    client = MQTTClient('ME35_chris', mqtt_broker, 1883)
    client.set_callback(callback)  
    client.connect()
    print('Connected to MQTT broker')
    client.subscribe(topic_sub.encode())

    while True:
        client.check_msg()  # Check for MQTT messages
        await asyncio.sleep(0.1) 

# ---------------------------------Main--------------------------------
async def main():
    gc.collect()
    
    breathe_task = asyncio.create_task(breathe())
    toggle_light_task = asyncio.create_task(toggle_light())
    detect_tap_task = asyncio.create_task(detect_tap())
    mqtt_task = asyncio.create_task(mqtt_client()) 

    await asyncio.gather(breathe_task, toggle_light_task, detect_tap_task, mqtt_task)

asyncio.run(main())
