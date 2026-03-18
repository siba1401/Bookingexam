import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# This creates the standard Django application
application = get_wsgi_application()

# This tells WhiteNoise where to find the 'staticfiles' folder we created earlier
# We use BASE_DIR logic here to make it work specifically on Vercel's server
base_path = os.path.dirname(os.path.dirname(__file__))
static_root = os.path.join(base_path, 'staticfiles')

application = WhiteNoise(application, root=static_root)

# Vercel specifically looks for 'app' to start the project
app = application
