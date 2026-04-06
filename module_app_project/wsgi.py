"""
WSGI config for module_app_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module_app_project.settings')

# Get WSGI application
application = get_wsgi_application()

# Optional: For better performance, you can use a WSGI server like gunicorn
# application = get_wsgi_application()