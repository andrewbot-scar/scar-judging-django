"""
WSGI config for SCAR Judge Portal
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scar_judging.settings')
application = get_wsgi_application()
