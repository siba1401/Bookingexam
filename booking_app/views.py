from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import Faculty


def faculty_login_view(request):
    if request.method == "POST":
        login_input = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')

        # Authentication lookup
        user_obj = Faculty.objects.filter(email=login_input).first() or \
                   Faculty.objects.filter(username=login_input).first()

        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
            if user and user.is_active:
                # --- DIRECT LOGIN ENABLED ---
                auth_login(request, user)
                # Redirect to the main Booking table view
                return redirect('/admin/booking_app/booking/')

        messages.error(request, "Invalid Email or Password.")

    return render(request, 'admin/examiner_login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('faculty_login')


# Dummy view to prevent URL errors if 'verify_otp' is still linked elsewhere
def verify_otp_view(request):
    return redirect('faculty_login')