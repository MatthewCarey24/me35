import time
import uasyncio as asyncio
from machine import Pin
from BLE_CEEO import Yell
from mqtt import MQTTClient
import network
import random  # Added for random LED selection


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
midi_file = 'Seinfeld.mid'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('Tufts_Robot', '')

while wlan.ifconfig()[0] == '0.0.0.0':
    print('.', end=' ')
    time.sleep(1)

# We should have a valid IP now via DHCP
print(wlan.ifconfig())

# Initialize MIDI peripheral
p = Yell('Mattt', verbose=True, type='midi')
p.connect_up()

# Set up the pause button
pause_button = Pin(20, Pin.IN, Pin.PULL_UP)
paused = False

# Set up the LEDs
led1 = Pin(16, Pin.OUT)  # Adjust pin numbers as needed
led2 = Pin(17, Pin.OUT)
led3 = Pin(18, Pin.OUT)
led4 = Pin(19, Pin.OUT)
leds = [led1, led2, led3, led4]

# Initialize all LEDs to off
for led in leds:
    led.value(0)

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
        # Turn off all LEDs when stopping
        for led in leds:
            led.value(0)
    else:
        # Step 1: Remove square brackets and quotes
        msg_decoded = msg_decoded.strip("[]").replace("'", "")
        # Step 2: Split the string into individual parts
        msg_list = msg_decoded.split(', ')
        # Step 3: Split each part by colon
        parts = [msg.split(':') for msg in msg_list]
        # Determine which part to use for command and value
        command_index = 0 if float(parts[0][1].strip()) > float(parts[1][1].strip()) else 1
        
        command = parts[command_index][0].strip()  # 'up' or 'down'
        value = float(parts[command_index][1].strip())  # Convert the corresponding value to float
        if value > 0.5:  
            if command == 'up':
                # Increase volume
                if current_volume < 117:  # MIDI max volume
                    current_volume += 10  # Adjust the increment as needed
                    print(f"Volume increased to {current_volume}.")
            elif command == 'down':
                if current_volume > 10:  # MIDI min volume
                    current_volume -= 10  # Adjust the decrement as needed
                    print(f"Volume decreased to {current_volume}.")
                else:
                    current_volume = 0
            else:
                print("Value not greater than 0.5, skipping command.")

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
    payload = bytes([tsM, tsL, c, note, current_volume])
    p.send(payload)
    
    # Randomly select and light up an LED
    selected_led = random.choice(leds)
    for led in leds:  # Turn off all LEDs first
        led.value(0)
    selected_led.value(1)  # Turn on the selected LED
    
    await wait_with_pause(duration)
    
    # Note Off
    c = NoteOff | channel_mask
    payload = bytes([tsM, tsL, c, note, current_volume])
    p.send(payload)
    
    # Turn off the LED
    selected_led.value(0)

def read_variable_length(data, offset):
    """Read a variable-length value from MIDI data."""
    value = 0
    while True:
        byte = data[offset]
        value = (value << 7) | (byte & 0x7F)
        offset += 1
        if not (byte & 0x80):
            break
    return value, offset

def parse_midi_header(data):
    """Parse MIDI header to get format, tracks, and timing."""
    if data[0:4] != b'MThd':
        raise ValueError("Not a valid MIDI file")
    length = int.from_bytes(data[4:8], 'big')
    format_type = int.from_bytes(data[8:10], 'big')
    num_tracks = int.from_bytes(data[10:12], 'big')
    time_division = int.from_bytes(data[12:14], 'big')
    return format_type, num_tracks, time_division, 14  # Return offset to first track

def parse_midi_track(data, offset):
    """Parse a single MIDI track."""
    if data[offset:offset+4] != b'MTrk':
        raise ValueError("Invalid track header")
    track_length = int.from_bytes(data[offset+4:offset+8], 'big')
    offset += 8
    end_offset = offset + track_length
    
    events = []
    running_status = None
    while offset < end_offset:
        # Read delta time
        delta_time, offset = read_variable_length(data, offset)
        
        # Read event
        status = data[offset]
        if status & 0x80:  # Status byte
            running_status = status
            offset += 1
        else:  # Use running status
            status = running_status
        
        if status == NoteOn or status == NoteOff:
            note = data[offset]
            velocity = data[offset + 1]
            channel = status & 0x0F
            events.append((delta_time, status, channel, note, velocity))
            offset += 2
        else:
            # Skip other event types
            if status in [0xC0, 0xD0]:  # Program Change, Channel Pressure
                offset += 1
            elif status in [0x80, 0x90, 0xA0, 0xB0, 0xE0]:  # Other channel voice messages
                offset += 2
            elif status == 0xFF:  # Meta event
                type = data[offset]
                length, new_offset = read_variable_length(data, offset + 1)
                offset = new_offset + length
            else:
                offset += 1
    
    return events, end_offset

async def play_midi_file():
    while True:  # Main loop to keep playing the song
        try:
            with open(midi_file, 'rb') as f:
                midi_data = f.read()
        except OSError:
            print(f"Error: {midi_file} not found in the local directory.")
            return

        try:
            format_type, num_tracks, time_division, offset = parse_midi_header(midi_data)
            print(f"MIDI Format: {format_type}, Tracks: {num_tracks}, Division: {time_division}")
            
            for track_num in range(num_tracks):
                events, offset = parse_midi_track(midi_data, offset)
                
                current_time = 0
                for delta_time, status, channel, note, vel in events:
                    if not run_program or paused:
                        await asyncio.sleep(0.1)
                        continue
                    
                    delay = delta_time / time_division * 0.5  # Current tempo multiplier
                    if delay > 0:
                        await asyncio.sleep(delay)
                    
                    if status == NoteOn and vel > 0:
                        await play_note(note, 0.2, channel)
                    
                    current_time += delay
                
        except Exception as e:
            print(f"Error parsing MIDI file: {e}")
        
        # Turn off all LEDs between loops
        for led in leds:
            led.value(0)
            
        await asyncio.sleep(0.5)
        print("Restarting song...")


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