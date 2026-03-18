from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # Required for production static serving
from booking_app.views import (
    faculty_login_view,
    verify_otp_view,
    logout_view
)

urlpatterns = [
    # 1. Home Redirect
    path('', lambda request: redirect('admin:index'), name='home'),

    # 2. OTP Login Workflow (Must stay above admin.site.urls)
    path('admin/login/', faculty_login_view, name='faculty_login'),
    path('admin/verify-otp/', verify_otp_view, name='verify_otp'),
    path('admin/logout/', logout_view, name='manual_logout'),

    # 3. Branded Password Reset Workflow
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='admin/examiner/password_reset_form.html',
        html_email_template_name='admin/examiner/password_reset_email.html',
        subject_template_name='admin/examiner/password_reset_subject.txt'
    ), name='password_reset'),

    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='admin/examiner/password_reset_done.html'
    ), name='password_reset_done'),

    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='admin/examiner/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='admin/examiner/password_reset_complete.html'
    ), name='password_reset_complete'),

    # 4. Standard Auth & Main Admin
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
]

# --- PRODUCTION STATIC FILE HANDLING ---
# This ensures that even if WhiteNoise misses a file, Django can serve it
if not settings.DEBUG:
    urlpatterns += [
        path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    ]
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
