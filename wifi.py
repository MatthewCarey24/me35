import network
import time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('tufts_eecs', 'foundedin1883')

while wlan.ifconfig()[0] == '0.0.0.0':
    print('.', end=' ')
    time.sleep(1)

# We should have a valid IP now via DHCP
print(wlan.ifconfig())