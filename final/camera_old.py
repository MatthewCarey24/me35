import sensor
import time
import math
import random
import uasyncio as asyncio
import BLE_CEEO

# BLE Central
camera_ble = BLE_CEEO.Listen(name='Pico', verbose=True)

# Initialize sensor
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()

# Game mode and state
game_mode = 'red_light'
last_positions = {}
movement_detected = False

# Detect movement function
def detect_movement(tag_id, current_pos):
    if tag_id not in last_positions:
        return False
    last_pos = last_positions[tag_id]
    distance = math.sqrt((current_pos[0] - last_pos[0]) ** 2 + (current_pos[1] - last_pos[1]) ** 2)
    return distance > 10

# Async function to switch game mode
async def switch_game_mode():
    global game_mode
    while True:
        if game_mode == 'green_light':
            game_mode = 'red_light'
        elif game_mode == 'red_light':
            game_mode = 'green_light'
        
        print(f"Switching to {game_mode} mode.")
        await asyncio.sleep(random.uniform(2,6))  # Non-blocking sleep, allows other tasks to run

# Main async function
async def main():
    global movement_detected
    asyncio.create_task(switch_game_mode())
    camera_ble.connect_up()

    while camera_ble.is_connected:
        clock.tick()
        img = sensor.snapshot()
 
        for tag in img.find_apriltags():
            img.draw_rectangle(tag.rect, color=(255, 0, 0))
            img.draw_cross(tag.cx, tag.cy, color=(0, 255, 0))

            current_pos = (tag.cx, tag.cy)
            if detect_movement(tag.id(), current_pos):
                if game_mode == 'red_light':
                    print("Lost! Tag moved!")
                    camera_ble.send("movement_detected")
                    movement_detected = True

            last_positions[tag.id()] = current_pos

        if movement_detected:
            print("Ending game due to movement.")
            break

        await asyncio.sleep(0.1)

    camera_ble.disconnect()
    print("Game ended.")

# Run the async event loop
asyncio.run(main())
