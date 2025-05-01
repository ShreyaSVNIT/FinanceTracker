# +++++++++++ DJANGO +++++++++++
import os
import sys

# Add your project directory to the sys.path
path = '/home/shreyaashar123/FinanceTracker'
if path not in sys.path:
    sys.path.append(path)

# Set environment variable to tell Django where your settings.py is
os.environ['DJANGO_SETTINGS_MODULE'] = 'FinanceTracker.settings'

# Set environment variable for production settings
os.environ['DJANGO_DEBUG'] = 'False'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

