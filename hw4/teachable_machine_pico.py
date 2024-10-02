from BLE_CEEO import Yell
from machine import Pin, PWM
import time

# Motor control pins
IN1 = Pin(15, Pin.OUT)  # Control pin 1 for the motor
IN2 = Pin(16, Pin.OUT)  # Control pin 2 for the motor
pwm_pin = PWM(Pin(4))   # PWM pin to control motor speed
pwm_pin.freq(1000)      # Set PWM frequency

# Motor control functions
def motor_forward(speed):
    print("Motor starting")
    IN1.value(1)
    IN2.value(0)
    pwm_pin.duty_u16(int(speed * 65535 / 100))  # Set motor speed via PWM (0-100%)

def motor_stop():
    print("Motor stopping")
    IN1.value(0)
    IN2.value(0)
    pwm_pin.duty_u16(0)  # Stop the motor by setting PWM duty to 0

# Function to handle BLE communication
def peripheral(name): 
    try:
        p = Yell(name, verbose=True)  # Initialize BLE peripheral
        if p.connect_up():  # Wait for connection
            print('BLE connected')
            time.sleep(2)  # Short delay after connection
            
            while True:
                if p.is_any:  # Check if there's a message to read
                    message = p.read()  # Read the BLE message
                    
                    # Example message format: 'Start: 1.00, Stop: 0.00'
                    # Split the string into key-value pairs
                    predictions = message.split(',')  # Split the string by ','
                    
                    for prediction in predictions:
                        command, value = prediction.split(':')  # Split by ': ' to get command and value
                        value = float(value)  # Convert the value to a float
                        
                        # Check if the command is 'Start' or 'Stop' and act accordingly
                        if command == 'Start' and value > 0.6:  # If 'Start' with value 1.00
                            motor_forward(80)  # Start motor at 80% speed
                        elif command == 'Stop' and value > 0.6:  # If 'Stop' with value 1.00
                            motor_stop()  # Stop the motor

                if not p.is_connected:  # If BLE connection is lost
                    print('BLE connection lost')
                    break
                
                time.sleep(1)  # Wait between BLE reads

    except Exception as e:
        print(f"Error: {e}")
    finally:
        p.disconnect()
        print('BLE connection closed')

# Run the BLE motor control
peripheral('Matt')  
