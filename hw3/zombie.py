import time
from Tufts_ble import Sniff, Yell
from machine import Pin, PWM
import neopixel

# Define buzzer pin and Neopixel pin
buzzer = PWM(Pin('GPIO18', Pin.OUT))
button = Pin('GPIO20', Pin.IN)

def zombie():
    p = Yell()

    try:
        p.set_tx_power(4)  # Adjust this value based on your hardware capability
    except AttributeError:
        print("TX power adjustment not supported on this device.")

    buzzer.freq(1000) 
    buzzer.duty_u16(32768)  # 50% duty cycle (volume)

    state = (255, 0, 0)  # RGB
    led = neopixel.NeoPixel(Pin(28),1)

    while button.value():
        led[0] = state
        led.write()

        p.advertise(f'!{3}')  # Broadcasting signal

        time.sleep(0.02)  # 20ms between broadcasts
    
    # Cleanup
    p.stop_advertising()
    buzzer.duty_u16(0)  
    led[0] = (0, 0, 0)
    led.write()

zombie()