from django.urls import re_path
from .consumers import BotConsumer
from .runner_consumers import RunnerConsumer

websocket_urlpatterns = [
    re_path(r'ws/bot/$', BotConsumer.as_asgi()),
    re_path(r'ws/runner/$', RunnerConsumer.as_asgi()),
]
