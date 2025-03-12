from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/mqtt/(?P<deviceID>[\w-]+)/$", consumers.MqttConsumer.as_asgi()),
]
