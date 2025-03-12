from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MqttConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.deviceID = self.scope["url_route"]["kwargs"]["deviceID"]
        self.group_name = f"mqtt_{self.deviceID}"  # Unique group for each device
        
        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            pass

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception as e:
            pass

    async def mqtt_message(self, event):
        print(f"📡 Received event from Channels: {event}")  # DEBUG
        try:
            await self.send(text_data=json.dumps({
                "message": event["message"],
                "deviceID": event["deviceID"]
            }))
        except Exception as e:
            pass
