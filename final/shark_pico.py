from machine import Pin, PWM, deepsleep
import time
import BLE_CEEO as BLE_CEEO

# Setup
buzzer = PWM(Pin(18, Pin.OUT))
led_2 = Pin(16, Pin.OUT)
led_1 = Pin(17, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_DOWN)

# BLE Peripheral
pico_ble = BLE_CEEO.Yell(name='Pico', verbose=True)

# Globals
game_active = False

# Function to handle received BLE messages
def on_ble_rx(data):
    global game_active
    message = data.decode('utf-8')
    print(f"Received message: {message}")
    
    if message == "movement_detected" and game_active:
        print("Movement detected! Buzzing and flashing red.")
        flash_red()
        buzz()
        end_game()
    elif message == "red_light" and game_active:
        led_2.on()
        led_1.on()
    elif message == "green_light":
        led_1.off()
        led_2.off()

# Function to buzz
def buzz():
    buzzer.freq(1000)
    buzzer.duty_u16(30000)
    time.sleep(0.5)
    buzzer.duty_u16(0)

# Function to buzz with a happy sound
def buzz_happy():
    melody = [262, 294, 330, 349, 392]  # Notes: C, D, E, F, G
    duration = 0.2

    for note in melody:
        buzzer.freq(note)
        buzzer.duty_u16(30000)
        time.sleep(duration)
        buzzer.duty_u16(0)
        time.sleep(0.05)

# Function to flash red LED
def flash_red():
    for _ in range(3):
        led_2.on()
        led_1.on()
        time.sleep(0.3)
        led_2.off()
        led_1.off()
        time.sleep(0.3)

# Function to check button press
def button_pressed():
    return button.value() == 1

# Start game
def start_game():
    global game_active
    print("Game started!")
    game_active = True

# End game
def end_game():
    global game_active
    print("Game ended.")
    game_active = False
    buzz_happy()  # Play the happy sound

# Idle mode waiting for button press
def idle_mode():
    print("Idle mode. Press the button to start the game.")
    led_2.on()
    while not button_pressed():
        time.sleep(0.1)

# Ensure BLE connection
def ensure_ble_connection():
    print("Ensuring BLE connection...")
    while not pico_ble.is_connected:
        print("Attempting to connect...")
        pico_ble.connect_up()
        if pico_ble.is_connected:
            print("Connected successfully.")
        else:
            print("Connection failed. Retrying in 1 second...")
            time.sleep(1)

# Main program
if __name__ == "__main__":
    pico_ble._write_callback = on_ble_rx
    ensure_ble_connection()  # Establish and maintain BLE connection

    while True:
        if not game_active:
            idle_mode()  # Wait for button press to start the game
            start_game()  # Begin the game
        else:
            if button_pressed():
                print("Button pressed during game!")
                end_game()  # End the game on button press

        # Keep the program alive and BLE communication running
        time.sleep(0.1)
