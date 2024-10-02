import network
from mqtt import MQTTClient
from machine import Pin, PWM
import uasyncio as asyncio  # Use MicroPython's version of asyncio

# Define motor control pins
IN1 = Pin(20, Pin.OUT)
IN2 = Pin(21, Pin.OUT)
pwm_pin = PWM(Pin(4))
pwm_pin.freq(1000)

# Motor control functions with prints
async def motor_forward(speed):
    print(f"Motor moving forward with speed {speed}%")
    IN1.value(1)
    IN2.value(0)
    pwm_pin.duty_u16(int(speed * 65535 / 100))

async def motor_backward(speed):
    print(f"Motor moving backward with speed {speed}%")
    IN1.value(0)
    IN2.value(1)
    pwm_pin.duty_u16(int(speed * 65535 / 100))

async def motor_stop():
    print("Motor stopping")
    IN1.value(0)
    IN2.value(0)
    pwm_pin.duty_u16(0)

# MQTT callback with print statements
def callback(topic, msg):
    command = msg.decode()
    print(f"Received MQTT message on topic {topic.decode()}: {command}")
    if command == 'turn_left':
        print("Command: turn_left -> Motor stop")
        asyncio.create_task(motor_stop())
    elif command == 'backwards':
        print("Command: backwards -> Motor backward")
        asyncio.create_task(motor_backward(80))
    else:
        print("No valid command received -> Motor moving forward")
        asyncio.create_task(motor_forward(80))

# Network connection with prints
async def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('Tufts_Robot', '')
    print("Connecting to WiFi...")
    while wlan.ifconfig()[0] == '0.0.0.0':
        print("Waiting for WiFi connection...")
        await asyncio.sleep(1)
    print("Connected to WiFi! IP Address:", wlan.ifconfig())

# MQTT handler with prints
async def mqtt_handler(client):
    print("Starting MQTT message handler")
    while True:
        try: 
            client.check_msg()
        except OSError as e:
            print(f"MQTT Error: {e}")
        await asyncio.sleep(1)

# Main function with prints
async def main():
    print("Starting main function")
    await connect_to_wifi()

    mqtt_broker = 'broker.hivemq.com'
    port = 1883
    topic_sub = 'ME35-24/camera-test'

    print(f"Setting up MQTT client to connect to broker {mqtt_broker} on port {port}")
    client = MQTTClient('ME35_right_motor', mqtt_broker, port, keepalive=60)
    client.set_callback(callback)

    try:
        print("Connecting to MQTT broker...")
        client.connect()
        print("Connected to MQTT broker")
        client.subscribe(topic_sub.encode())
        print(f"Subscribed to topic: {topic_sub}")
    except OSError as e:
        print(f"MQTT Connection failed: {e}")
        return

    # Start handling MQTT messages
    print("Starting MQTT message handling loop")
    await mqtt_handler(client)

# Run the main async function using MicroPython's asyncio
try:
    print("Running asyncio loop")
    asyncio.run(main())  # MicroPython-compatible asyncio.run()
except MemoryError:
    print("MemoryError: Restarting...")
    machine.reset()
