import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env at the very top
load_dotenv()
FAST2SMS_KEY = os.getenv('FAST2SMS_API_KEY')

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'your-fallback-key')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.vercel.app']
#ALLOWED_HOSTS = ['localhost','127.0.0.1','10.125.66.231','.onrender.com',  # This allows all subdomains on Render]

INSTALLED_APPS = [
    #'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'booking_app',
]

# CRITICAL: Order matters here to fix your E408, E409, E410 errors
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Must be before Auth
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Required for Admin
    'django.contrib.messages.middleware.MessageMiddleware', # Required for Admin
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
AUTH_USER_MODEL = 'booking_app.Faculty'
WSGI_APPLICATION = 'core.wsgi.application'

import dj_database_url

# Use Render's DB if available, otherwise fallback to your local Postgres
#DATABASES = {
    #'default': dj_database_url.config(
        #default=os.getenv('DATABASE_URL', 'postgres://postgres:admin1401@127.0.0.1:5432/booking_db'),
        #conn_max_age=600
    #)
#}

import dj_database_url

# This tries to get 'DATABASE_URL' from Vercel/Neon environment variables
# If it doesn't find it, it falls back to your local manual config
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Manual fallback for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'booking_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'admin1401'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

# Fixes E403: Admin needs this exact structure
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Add this check so the build doesn't crash if 'static' folder is missing
STATIC_STATIC_DIR = BASE_DIR / "static"
if STATIC_STATIC_DIR.exists():
    STATICFILES_DIRS = [STATIC_STATIC_DIR]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"



# --- EMAIL CONFIG (Fixes ConnectionRefusedError) ---
# For testing without a crash, use 'console'. Change to 'smtp' for real emails.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# --- Jazzmin Traditional Look ---
# core/settings.py
JAZZMIN_SETTINGS = {
    "site_title": "NMIMS Admin",
    "site_header": "NMIMS Portal",
    "site_brand": "NMIMS EXAM PORTAL",
    "site_logo": "images/university_logo.png",
    "login_logo": "images/university_logo.png",
    "welcome_sign": "Authorized Access: NMIMS Examination Portal",
    "copyright": "SVKM's NMIMS 2026",  # Added official university prefix
    "search_model": ["booking_app.Examiner", "booking_app.Booking"],  # Expanded search
    "user_avatar": None,

    "changeform_format": "horizontal_tabs",
    "navigation_expanded": True,
    "show_sidebar": True,
    "show_ui_builder": False,

    # Professional top-menu links
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "mailto:support@nmims.edu", "new_window": True},
        {"model": "booking_app.Booking"},
    ],

    "custom_links": {
        "booking_app": [
            {
                "name": "Live Booking Dashboard",
                "url": "admin:booking_dashboard",
                "icon": "fas fa-chalkboard-teacher",
                "permissions": ["booking_app.view_booking"]
            },
        ],
    },

    "icons": {
        "auth.user": "fas fa-user-shield",
        "booking_app.Faculty": "fas fa-chalkboard-teacher",
        "booking_app.Examiner": "fas fa-user-tie",
        "booking_app.Booking": "fas fa-list-alt",  # Changed for variety
    },

    "default_ui_tweaks": {
        "navbar": "navbar-navy navbar-dark",
        "sidebar": "sidebar-light-navy",
        "accent": "accent-navy",
        "navbar_fixed": True,
        "sidebar_fixed": True,
        "brand_colour": "navbar-navy",
        "body_small_text": False,
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",  # Professional academic typography
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Django 6.0 Compatibility
from django.utils import html
from django.utils.safestring import mark_safe
_orig = html.format_html
def patched(*args, **kwargs):
    if len(args) == 1 and not kwargs: return mark_safe(args[0])
    return _orig(*args, **kwargs)
html.format_html = patched


WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
