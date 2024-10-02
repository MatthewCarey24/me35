#Code to run on PC for Teachable Machine Joystick
from pyscript.js_modules import teach, pose, ble_library

ble = ble_library.newBLE()

async def run_model(URL2):
    s = teach.s  # or s = pose.s
    s.URL2 = URL2
    await s.init()
    
async def connect(name):
    if await ble.ask(name):
        print('name ',name)
        await ble.connect() 
        print('connected!')
        
async def disconnect():
    await ble.disconnect()
    print('disconnected')

def send(message):
    print('sending ', message)
    ble.write(message)

def get_predictions(num_classes):
    predictions = []
    for i in range (0,num_classes):
        divElement = document.getElementById('class' + str(i))
        if divElement:
            divValue = divElement.innerHTML
            predictions.append(divValue)
    return predictions


import asyncio
await run_model("https://teachablemachine.withgoogle.com/models/Ti7ITJPKG/") #Change to your model link
await connect('Matt')

while True:
    if ble.connected:
        predictions = get_predictions(2)
        send(predictions)
    await asyncio.sleep(2)