import time
import uasyncio as asyncio
from machine import Pin
from BLE_CEEO import Yell
from mqtt import MQTTClient

# MIDI message constants
NoteOn = 0x90
NoteOff = 0x80

# Note velocity
velocity = {
    'mf': 64  # We'll use a medium volume for all notes
}

# MQTT Settings
mqtt_broker = 'broker.hivemq.com'
topic_sub = 'ME35-24/stu'
run_program = False

# MIDI file settings
midi_file = 'Seinfeld.mid'  # Change this to the name of your MIDI file

# Initialize MIDI peripheral
p = Yell('Mattt', verbose=True, type='midi')
p.connect_up()

# Set up the pause button
pause_button = Pin(20, Pin.IN, Pin.PULL_UP)
paused = False

def toggle_pause(pin):
    global paused
    paused = not paused
    print("Paused" if paused else "Resumed")

pause_button.irq(trigger=Pin.IRQ_FALLING, handler=toggle_pause)

# Global variable for volume
current_volume = velocity['mf']

def mqtt_callback(topic, msg):
    global run_program, current_volume
    msg_decoded = msg.decode().strip()  # Clean up any whitespace
    if msg_decoded == 'start':
        run_program = True
        print("Program started via MQTT.")
    elif msg_decoded == 'stop':
        run_program = False
        print("Program stopped via MQTT.")
    else:
        parts = msg_decoded.split(':')
        if len(parts) == 2:
            command = parts[0].strip()
            try:
                value = float(parts[1].strip())  # Convert the value to float
                if value > 0.5:  # Check if the value is greater than 0.5
                    if command == 'up':
                    # Increase volume
                        if current_volume < 127:  # MIDI max volume
                            current_volume += 10  # Adjust the increment as needed
                            print(f"Volume increased to {current_volume}.")
                    elif command == 'down':
                        if current_volume > 0:  # MIDI min volume
                            current_volume -= 10  # Adjust the decrement as needed
                            print(f"Volume decreased to {current_volume}.")
                else:
                    print("Value not greater than 0.5, skipping command.")
            except ValueError:
                print("Invalid value received, skipping.")
                return  # Skip if conversion fails


    

async def wait_with_pause(duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        if paused or not run_program:
            await asyncio.sleep(0.1)
        else:
            await asyncio.sleep(0.1)
            if time.time() >= end_time:
                break

async def play_note(note, duration, channel=0):
    timestamp_ms = time.ticks_ms()

    channel_mask = 0x0F & channel
    tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
    tsL = 0x80 | (timestamp_ms & 0b1111111)

    # Note On
    c = NoteOn | channel_mask
    payload = bytes([tsM, tsL, c, note, current_volume])  # Use current_volume here
    p.send(payload)
    
    await wait_with_pause(duration)
    
    # Note Off
    c = NoteOff | channel_mask
    payload = bytes([tsM, tsL, c, note, current_volume])  
    p.send(payload)


async def play_midi_file():
    try:
        with open(midi_file, 'rb') as f:
            midi_data = f.read()
    except OSError:
        print(f"Error: {midi_file} not found in the local directory.")
        return

    # Parse MIDI file and extract note events
    # (This is a simplified implementation, real MIDI parsing is more complex)
    time_delta = 0
    channel = 0
    for i in range(14, len(midi_data), 4):
        delta_time = midi_data[i]
        note = midi_data[i + 1]
        duration = midi_data[i + 2] / 10  # Assuming a fixed duration here
        time_delta += delta_time
        if run_program and not paused:
            await play_note(note, duration, channel)
        await asyncio.sleep(time_delta / 1000)
        time_delta = 0

async def mqtt_client():
    client = MQTTClient('ME35_matt', mqtt_broker, 1883)
    client.set_callback(mqtt_callback)  
    client.connect()
    print('Connected to MQTT broker')
    client.subscribe(topic_sub.encode())
    while True:
        client.check_msg()  
        await asyncio.sleep(0.1) 

async def main():
    play_task = asyncio.create_task(play_midi_file())
    mqtt_task = asyncio.create_task(mqtt_client())
    
    try:
        await asyncio.gather(play_task, mqtt_task)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        p.disconnect()

asyncio.run(main())