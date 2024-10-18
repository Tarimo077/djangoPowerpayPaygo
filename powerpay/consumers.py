from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MqttConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.channel_layer.group_add("mqtt_group", self.channel_name)
            await self.accept()
            print(f"WebSocket connected: {self.channel_name}")
        except Exception as e:
            print(f"Error connecting WebSocket: {e}")

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard("mqtt_group", self.channel_name)
            print(f"WebSocket disconnected: {self.channel_name}")
        except Exception as e:
            print(f"Error disconnecting WebSocket: {e}")

    async def mqtt_message(self, event):
        message = event["message"]
        try:
            await self.send(text_data=json.dumps({"message": message}))
            print(f"Message sent to WebSocket: {message}")
        except Exception as e:
            print(f"Error sending message to WebSocket: {e}")
