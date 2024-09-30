from machine import Pin, PWM
import neopixel
import uasyncio as asyncio
from mqtt import MQTTClient
import gc

# MQTT Settings
mqtt_broker = 'broker.hivemq.com'
topic_sub = 'ME35-24/camera-test'

run_program = False

def callback(topic, msg):
    global run_program
    msg_decoded = msg.decode()
    
    if msg_decoded == 'start':
        run_program = True
        print("Program started via MQTT.")
    elif msg_decoded == 'stop':
        run_program = False
        print("Program stopped via MQTT.")

    print(msg_decoded)

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

# ---------------------------------Buzzer-----------------------------
async def sound_buzzer():
    button = Pin(20, Pin.IN)
    f = PWM(Pin(18, Pin.OUT))
    f.freq(440)
    pressed_color = (10,0,10)
    resting_color = (0,0,0)

    led = neopixel.NeoPixel(Pin(28),1)

    while True:
        if run_program:
            if not button.value():
                led[0] = pressed_color
                led.write()
                f.duty_u16(1000)
            else:
                led[0] = resting_color
                led.write()
                f.duty_u16(0)
        await asyncio.sleep(0.01)

# ---------------------------------MQTT-----------------------------
async def mqtt_client():
    client = MQTTClient('ME35_chris', mqtt_broker, 1883)
    client.set_callback(callback)  
    client.connect()
    print('Connected to MQTT broker')
    client.subscribe(topic_sub.encode())

    while True:
        client.check_msg()  
        await asyncio.sleep(0.1) 

async def main():
    gc.collect()
    
    breathe_task = asyncio.create_task(breathe())
    monitor_buzzer_button = asyncio.create_task(sound_buzzer())
    mqtt_task = asyncio.create_task(mqtt_client()) 

    await asyncio.gather(breathe_task, monitor_buzzer_button, mqtt_task)

asyncio.run(main())
