from BLE_CEEO import Yell
from machine import Pin, PWM
import time
import network
from mqtt import MQTTClient
import uasyncio as asyncio  # Use MicroPython's version of asyncio

# Wi-Fi configuration
SSID = 'Tufts_Robot'          
PASSWORD = ''   

# Motor control pins
IN1 = Pin(15, Pin.OUT)
IN2 = Pin(16, Pin.OUT)
pwm_pin = PWM(Pin(4))   
pwm_pin.freq(1000)

# Global variable to control motor operation based on BLE
run_motor = False

# Function to connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print('Connecting to Wi-Fi...')
    while not wlan.isconnected():
        time.sleep(1)
    
    print('Wi-Fi connected:', wlan.ifconfig())

# Motor control functions
def motor_forward(speed):
    if run_motor:
        print("Motor moving forward")
        IN1.value(1)
        IN2.value(0)
        pwm_pin.duty_u16(int(speed * 65535 / 100))  
    else:
        print("Motor is stopped by BLE")

def motor_backward(speed):
    if run_motor:
        print("Motor moving backward")
        IN1.value(0)
        IN2.value(1)
        pwm_pin.duty_u16(int(speed * 65535 / 100))  
    else:
        print("Motor is stopped by BLE")

def motor_stop():
    print("Motor stopping")
    IN1.value(0)
    IN2.value(0)
    pwm_pin.duty_u16(0)  

# BLE communication task
async def ble_peripheral(name): 
    global run_motor  
    try:
        p = Yell(name, verbose=True)
        if p.connect_up():
            print('BLE connected')
            await asyncio.sleep(2)  # Short delay after connection
            
            while True:
                if p.is_any:
                    message = p.read()  
                    print(f"Received BLE message: {message}")
                    
                    predictions = message.split(',')  
                    
                    for prediction in predictions:
                        command, value = prediction.split(':')  
                        value = float(value)  
                        
                        if command == 'Start' and value >= 0.6:
                            print("BLE: Motor enabled")
                            run_motor = True  
                        elif command == 'Stop' and value >= 0.6:
                            print("BLE: Motor disabled")
                            run_motor = False  
                        
                if not p.is_connected:
                    print('BLE connection lost')
                    break
                
                await asyncio.sleep(1)  

    except Exception as e:
        print(f"Error: {e}")
    finally:
        p.disconnect()
        print('BLE connection closed')

# MQTT callback function
def mqtt_callback(topic, msg):
    global run_motor  
    if not run_motor:
        print("Motor is stopped by BLE, ignoring MQTT commands.")
        return

    if msg == b'turn':
        print("MQTT: Turning motor")
        motor_forward(50)
    elif msg == b'backward':
        print("MQTT: Moving motor backward")
        motor_backward(80)
    else:
        print(f"MQTT: Unknown command: {msg}")

# MQTT setup function
def mqtt_setup():
    mqtt_broker = 'broker.hivemq.com'
    port = 1883
    topic_sub = 'ME35-24/camera-test'
    client = MQTTClient('ME35_right_motor', mqtt_broker, port, keepalive=30)
    client.set_callback(mqtt_callback)
    client.connect()  
    client.subscribe(topic_sub.encode())  
    return client

# Main loop
async def main():
    connect_wifi()
    
    # Start BLE peripheral as a task
    asyncio.create_task(ble_peripheral('Matt'))
    print("BLE peripheral task started.")
    
    # Set up MQTT
    client = mqtt_setup()
    
    while True:
        client.check_msg()  
        await asyncio.sleep(0.5)

# Start the event loop
asyncio.run(main())
