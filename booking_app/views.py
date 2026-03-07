import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
from .models import Faculty


def faculty_login_view(request):
    if request.method == "POST":
        # Updated to 'email' to match your professional template's name="email"
        login_input = request.POST.get('email', '').strip().lower()
        p = request.POST.get('password')

        # 1. Look for the user (Faculty model) by email or username
        user_obj = Faculty.objects.filter(email=login_input).first() or \
                   Faculty.objects.filter(username=login_input).first()

        if user_obj:
            # 2. Authenticate using the username found in the database
            user = authenticate(request, username=user_obj.username, password=p)
        else:
            user = None

        if user and user.is_active:
            # --- OTP Logic ---
            otp_code = str(random.randint(100000, 999999))
            user.otp = otp_code
            user.otp_created_at = timezone.now()
            user.save()

            # For testing: prints OTP to your terminal
            print(f"DEBUG OTP for {user.email}: {otp_code}")

            try:
                send_mail(
                    'MPSTME Examiner Portal OTP',
                    f'Your secure login code is: {otp_code}',
                    'noreply@nmims.edu',
                    [user.email]
                )
            except Exception as e:
                print(f"Mail Error: {e}")

            request.session['pre_otp_user_id'] = user.id
            return redirect('verify_otp')

        # If authentication fails
        messages.error(request, "Invalid Email or Password. Please try again.")

    # Render your new professional login template
    return render(request, 'admin/examiner_login.html')


def verify_otp_view(request):
    user_id = request.session.get('pre_otp_user_id')
    if not user_id:
        return redirect('faculty_login')

    if request.method == "POST":
        entered = request.POST.get('otp')
        try:
            user = Faculty.objects.get(id=user_id)
            if user.otp == entered and user.is_otp_valid():
                auth_login(request, user)
                # Clear the session variable after successful login
                del request.session['pre_otp_user_id']
                return redirect('/admin/booking_app/booking/dashboard/')
            else:
                messages.error(request, "The OTP entered is invalid or has expired.")
        except Faculty.DoesNotExist:
            return redirect('faculty_login')

    return render(request, 'admin/verify_otp.html')


def logout_view(request):
    auth_logout(request)
    return redirect('faculty_login')