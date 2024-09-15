import time
from mqtt import MQTTClient

mqtt_broker = 'broker.hivemq.com' 
port = 1883
topic_sub = 'ME35-24/#'       # this reads anything sent to ME35
topic_pub = 'ME35-24/tell'


def callback(topic, msg):
    print((topic.decode(), msg.decode()))

client = MQTTClient('ME35_chris', mqtt_broker , port, keepalive=60)
client.connect()
print('Connected to %s MQTT broker' % (mqtt_broker))
client.set_callback(callback)          # set the callback if anything is read
client.subscribe(topic_sub.encode())   # subscribe to a bunch of topics

msg = 'this is a test'
i = 0
while True:
    i+=1
    if i %5 == 0:
        print('publishing')
        client.publish(topic_pub.encode(),msg.encode())
    client.check_msg()
    time.sleep(1)