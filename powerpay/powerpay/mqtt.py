import paho.mqtt.client as mqtt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        mqtt_client.subscribe('/testTopic')
    else:
        print('Bad connection. Code:', rc)


def on_message(client, userdata, msg):
    print(f"Message received: {msg.payload.decode()}")
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "mqtt_group",
        {
            "type": "mqtt_message",
            "message": msg.payload.decode(),
        }
    )

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("admin", "123Give!@#")
client.connect("mqttpowerpay.xyz", 1883)

client.loop_start()  # This will allow the client to run in a separate thread
