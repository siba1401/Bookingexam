import pandas as pd
from datetime import datetime, timedelta
from django.contrib import admin, messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.admin import UserAdmin
from .models import Examiner, Faculty, Booking

# Global Admin Branding
admin.site.site_header = "NMIMS Exam Admin"
admin.site.site_title = "NMIMS Portal"
admin.site.index_title = "Welcome to the Examiner Enrollment Portal"


@admin.register(Faculty)
class ExamDeptAdmin(UserAdmin):
    list_display = ('username', 'department', 'bulk_upload_link')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'department')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    class Media:
        js = (
            'admin/js/vendor/jquery/jquery.js',
            'admin/js/jquery.init.js',
        )

    def bulk_upload_link(self, obj=None):
        url = reverse('admin:faculty_bulk_upload')
        return format_html(
            '<a class="button" style="background:#007bff; color:white; padding:5px 10px; border-radius:4px; font-weight:bold;" href="{}">Bulk Upload</a>',
            url)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload-faculty/', self.admin_site.admin_view(self.bulk_upload_faculty),
                 name='faculty_bulk_upload')
        ]
        return custom_urls + urls

    def bulk_upload_faculty(self, request):
        if request.method == "POST":
            file = request.FILES.get('excel_file')
            if not file:
                messages.error(request, "Please upload an Excel file.")
                return redirect("admin:faculty_bulk_upload")
            try:
                df = pd.read_excel(file)
                count = 0
                for _, row in df.iterrows():
                    username = str(row['username']).strip().lower()
                    user, created = Faculty.objects.get_or_create(username=username)
                    user.email = row.get('email')
                    user.department = row.get('department')
                    if created or not user.has_usable_password():
                        user.set_password("password123")
                    user.is_staff = True
                    user.is_active = True
                    user.save()
                    count += 1
                messages.success(request, f"Successfully imported {count} faculty members.")
                return redirect("admin:booking_app_faculty_changelist")
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
        return render(request, 'admin/bulk_upload.html', {'title': 'Bulk Upload Exam Department User'})


@admin.register(Examiner)
class ExaminerAdmin(admin.ModelAdmin):
    list_display = ('name', 'sap_vendor_code', 'upload_button')

    def upload_button(self, obj=None):
        url = reverse('admin:examiner_bulk_upload')
        return format_html(
            '<a class="button" style="background:#28a745; color:white; padding:5px 10px; border-radius:4px; font-weight:bold;" href="{}">Bulk Upload</a>',
            url)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload-examiner/', self.admin_site.admin_view(self.bulk_upload_examiner),
                 name='examiner_bulk_upload')
        ]
        return custom_urls + urls

    def bulk_upload_examiner(self, request):
        if request.method == "POST":
            file = request.FILES.get('excel_file')
            try:
                df = pd.read_excel(file)
                for _, row in df.iterrows():
                    Examiner.objects.get_or_create(
                        sap_vendor_code=str(row['sap_vendor_code']).strip(),
                        defaults={'name': row['name']}
                    )
                messages.success(request, "Supervisor imported successfully.")
                return redirect("admin:booking_app_examiner_changelist")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return render(request, 'admin/bulk_upload.html', {'title': 'Bulk Upload Supervisor'})


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    change_list_template = "admin/examiner/change_list.html"
    # Added school_name to list_display
    list_display = ('booked_by', 'examiner', 'school_name', 'date', 'slot', 'is_paid', 'transaction_id', 'display_total_amount')
    search_fields = ('booked_by__username', 'examiner__name', 'transaction_id', 'school_name')
    # Added school_name to list_filter
    list_filter = ('school_name', 'date', 'slot', 'is_paid')

    # --- PERMISSIONS & AUTO-ASSIGNMENT ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(booked_by=request.user)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser and obj.booked_by != request.user:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser and obj.booked_by != request.user:
            return False
        return super().has_delete_permission(request, obj)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            return [f for f in fields if f != 'booked_by']
        return fields

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if 'examiner' in request.GET:
            initial['examiner'] = request.GET.get('examiner')
        if 'date' in request.GET:
            initial['date'] = request.GET.get('date')
        if 'slot' in request.GET:
            initial['slot'] = request.GET.get('slot')
        return initial

    def save_model(self, request, obj, form, change):
        if not change:
            if not request.user.is_superuser:
                obj.booked_by = request.user

            # Check if this user (Exam Dept) has already booked a supervisor for this specific slot
            conflict = Booking.objects.filter(
                booked_by=obj.booked_by,
                date=obj.date,
                slot=obj.slot
            ).exists()
            if conflict:
                messages.error(request, f"Conflict: You already have a booking on {obj.date} at {obj.slot}.")
                return
        super().save_model(request, obj, form, change)

    # --- METHODS ---
    def display_total_amount(self, obj):
        return obj.total_amount

    display_total_amount.short_description = "Total Amount"

    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse('admin:booking_success', args=[obj.id]))

    def response_change(self, request, obj):
        return redirect(reverse('admin:booking_success', args=[obj.id]))

    actions = ["export_to_excel"]

    def export_to_excel(self, request, queryset=None):
        if queryset is None:
            queryset = Booking.objects.all()

        if not queryset.exists():
            messages.warning(request, "No data available to export.")
            return redirect(request.META.get('HTTP_REFERER', 'admin:booking_dashboard'))

        data = []
        for b in queryset:
            data.append({
                "Booked By": b.booked_by.username if b.booked_by else "N/A",
                "School": b.get_school_name_display(), # Shows full name from choices
                "Examiner": b.examiner.name,
                "Date": b.date,
                "Slot": b.slot,
                "Paid Status": "Yes" if b.is_paid else "No",
                "Transaction ID": b.transaction_id or "N/A",
                "Total Amount": b.total_amount
            })
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=Booking_Report_{timezone.now().date()}.xlsx'
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return response

    export_to_excel.short_description = "Export Selected to Excel"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.booking_dashboard), name='booking_dashboard'),
            path('export-excel-report/', self.admin_site.admin_view(self.export_to_excel),
                 name='export_all_bookings_excel'),
            path('<int:booking_id>/success/', self.admin_site.admin_view(self.booking_success_view),
                 name='booking_success'),
        ]
        return custom_urls + urls

    def booking_success_view(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        return render(request, 'admin/booking_success.html',
                      {**self.admin_site.each_context(request), 'booking': booking})

    def booking_dashboard(self, request):
        date_str = request.GET.get('date')
        ex_id = request.GET.get('examiner_id')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
        week_days = [selected_date - timedelta(days=selected_date.weekday()) + timedelta(days=i) for i in range(7)]
        all_examiners = Examiner.objects.all()
        examiners = all_examiners.filter(id=ex_id) if ex_id else all_examiners
        all_bookings = Booking.objects.filter(date__range=[week_days[0], week_days[-1]])

        for ex in examiners:
            ex.week_bookings = [b for b in all_bookings if b.examiner_id == ex.id]

        return render(request, 'admin/examiner/booking_dashboard.html', {
            **self.admin_site.each_context(request),
            'examiners': examiners,
            'all_examiners': all_examiners,
            'selected_date': selected_date,
            'selected_examiner': int(ex_id) if ex_id else None,
            'week_days': week_days,
            'slots': [c[0] for c in Booking.SLOT_CHOICES],
            'user_has_booked': False,
            'today': timezone.now().date(),
        })