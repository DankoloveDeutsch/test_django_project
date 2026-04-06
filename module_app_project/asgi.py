"""
ASGI config for module_app_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module_app_project.settings')

# Get ASGI application
application = get_asgi_application()

# Optional: For WebSocket support, you can add channels here
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
#
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter([
#             # WebSocket URL patterns
#         ])
#     ),
# })