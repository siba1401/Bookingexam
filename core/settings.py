import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Load .env at the very top
load_dotenv()
FAST2SMS_KEY = os.getenv('FAST2SMS_API_KEY')

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Optimized for Vercel
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.vercel.app', '.now.sh']

INSTALLED_APPS = [
    'jazzmin',  # Must be before admin
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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Best place for WhiteNoise
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
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
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

# --- STATIC FILES CONFIG (FIXED FOR JAZZMIN) ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Tell Django to look in the main 'static' folder if it exists
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []

# WhiteNoise settings to handle Jazzmin and production CSS
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False

# Ensure Django finds Jazzmin inside the site-packages
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# --- EMAIL CONFIG ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# --- JAZZMIN CONFIG ---
JAZZMIN_SETTINGS = {
    "site_title": "NMIMS Admin",
    
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

# --- PATCH FOR DJANGO 6.0 ---
from django.utils import html
from django.utils.safestring import mark_safe
_orig = html.format_html
def patched(*args, **kwargs):
    if len(args) == 1 and not kwargs: return mark_safe(args[0])
    return _orig(*args, **kwargs)
html.format_html = patched
