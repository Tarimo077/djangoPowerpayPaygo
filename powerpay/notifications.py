from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils.timezone import now
import pytz

def send_notification(user, title, message):
    """Function to send real-time notifications to a user"""
    channel_layer = get_channel_layer()
    
    # Use East Africa Time (EAT)
    eat = pytz.timezone('Africa/Nairobi')
    timestamp = now().astimezone(eat).strftime("%Y-%m-%d %H:%M:%S")
    
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}_notifications",
        {
            "type": "send_notification",
            "message": message,
            "timestamp": timestamp,
            "title": title,
        }
    )
