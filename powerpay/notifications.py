from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from datetime import datetime

def send_notification(user, title , message):
    """Function to send real-time notifications to a user"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}_notifications",
        {
            "type": "send_notification",
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": title,
        }
    )
