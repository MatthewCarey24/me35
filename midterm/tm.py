#Code to run on PC for Teachable Machine Joystick
from pyscript.js_modules import teach, pose, ble_library, mqtt_library

#ble = ble_library.newBLE()
myClient = mqtt_library.myClient
mqtt_connected = False
sub_topic = 'ME35-24/listen'
pub_topic = 'ME35-24/stu'

async def received_mqtt_msg(message):
    message = myClient.read().split('	')  #add here anything you want to do with received messages

async def run_model(URL2):
    s = teach.s  # or s = pose.s
    s.URL2 = URL2
    await s.init()
    
async def connect(name):
    global mqtt_connected
    myClient.init()
    while not myClient.connected:
        await asyncio.sleep(2)
    myClient.subscribe(sub_topic)
    myClient.callback = received_mqtt_msg
    mqtt_connected = True
    #if await ble.ask(name):
    #    print('name ',name)
    #    await ble.connect() 
    #    print('connected!')
        
async def disconnect():
    #await ble.disconnect()
    print('disconnected')

def send(message):
    print('sending ', message)
    myClient.publish(pub_topic, message)
    #ble.write(message)

def get_predictions(num_classes):
    predictions = []
    for i in range (0,num_classes):
        divElement = document.getElementById('class' + str(i))
        if divElement:
            divValue = divElement.innerHTML
            predictions.append(divValue)
    return predictions

import asyncio
await run_model("https://teachablemachine.withgoogle.com/models/ZQavQIj6G/") #Change to your model link
await connect('Sophie')

while True:
    if mqtt_connected:
        predictions = get_predictions(2)
        send(str(predictions))
    await asyncio.sleep(2)