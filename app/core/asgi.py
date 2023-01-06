from __future__ import absolute_import, unicode_literals

import os
import django


os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
# os.environ['DJANGO_CONFIGURATION'] = 'Dev'
django.setup()

from django.core.asgi import get_asgi_application
import chat.routing

# from configurations.asgi import get_asgi_application
from channels.sessions import SessionMiddlewareStack
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
# from configurations import importer
django_asgi_app = get_asgi_application()


# importer.install()


application = ProtocolTypeRouter({
  "http": django_asgi_app,
  "websocket": SessionMiddlewareStack(
        AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    chat.routing.websocket_urlpatterns
                )
            )
        )
    )
})
