import paho.mqtt.client as mqtt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        mqtt_client.subscribe('/testTopic/#')
    else:
        pass


def on_message(client, userdata, msg):
    topic_parts = msg.topic.split("/")  # Extract deviceID
    if len(topic_parts) < 3:
        return  # Ignore invalid topics

    deviceID = topic_parts[2]  # Extract deviceID from topic
    payload = msg.payload.decode()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"mqtt_{deviceID}",  # Unique group for each device
        {
            "type": "mqtt_message",
            "message": payload,
            "deviceID": deviceID,
        }
    )

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("admin", "123Give!@#")
client.connect("mqttpowerpay.xyz", 1883)

client.loop_start()  # This will allow the client to run in a separate thread
