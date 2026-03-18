import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# 1. Load Environment Variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-nmims-portal-2026')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.vercel.app', '.now.sh']

INSTALLED_APPS = [
    'jazzmin',  # Must be above admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'booking_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Required for Vercel CSS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
AUTH_USER_MODEL = 'booking_app.Faculty'
WSGI_APPLICATION = 'core.wsgi.application'

# --- DATABASE CONFIG ---
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=True)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'booking_db',
            'USER': 'postgres',
            'PASSWORD': 'password',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

# --- STATIC FILES (Vercel & Jazzmin Fix) ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# Simplified storage to prevent manifest errors with Jazzmin
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# --- FAST2SMS KEY ---
FAST2SMS_KEY = os.getenv('FAST2SMS_API_KEY')

# --- JAZZMIN CONFIG (Fixed for Rectangular Logo) ---
JAZZMIN_SETTINGS = {
    "site_title": "NMIMS Admin",
    "site_header": "NMIMS",
    "site_brand": "NMIMS PORTAL",
    "site_logo": "images/university_logo.png",
    "login_logo": "images/university_logo.png",
    "site_logo_classes": "img-fluid", # FIX: Use img-fluid instead of img-circle
    "site_icon": None,
    "welcome_sign": "Authorized Access: NMIMS Examination Portal",
    "copyright": "SVKM's NMIMS 2026",
    "user_avatar": None,
    "show_sidebar": True,
    "navigation_expanded": True,
    
    "icons": {
        "auth.user": "fas fa-user-shield",
        "booking_app.Faculty": "fas fa-chalkboard-teacher",
        "booking_app.Examiner": "fas fa-user-tie",
        "booking_app.Booking": "fas fa-calendar-check",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-navy navbar-dark",
    "sidebar": "sidebar-light-navy",
    "accent": "accent-navy",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "theme": "flatly",
    # CUSTOM CSS INJECTION TO REMOVE OVAL SHAPE
    "custom_css": None,
    "site_logo_classes": "img-fluid", 
}

# --- PATCH FOR DJANGO 6.0 ---
from django.utils import html
from django.utils.safestring import mark_safe
_orig = html.format_html
def patched(*args, **kwargs):
    if len(args) == 1 and not kwargs: return mark_safe(args[0])
    return _orig(*args, **kwargs)
html.format_html = patched
