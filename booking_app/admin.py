import io
import pandas as pd
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from django.db.models import Count, F
from django.conf import settings

# Import models from the current app
from .models import Examiner, Faculty, Booking, SMSLog


@admin.register(Faculty)
class ExamDeptAdmin(UserAdmin):
    list_display = ('username', 'school', 'bulk_upload_link')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'school')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def bulk_upload_link(self, obj=None):
        url = reverse('admin:faculty_bulk_upload')
        return format_html(
            '<a class="button" style="background:#003366; color:white; padding:5px 10px; border-radius:4px;" href="{}">Bulk Upload</a>',
            url)

    def get_urls(self):
        return [path('bulk-upload-faculty/', self.admin_site.admin_view(self.bulk_upload_faculty),
                     name='faculty_bulk_upload')] + super().get_urls()

    def bulk_upload_faculty(self, request):
        if request.method == "POST":
            file = request.FILES.get('excel_file')
            try:
                # Vercel fix: Read from memory
                df = pd.read_excel(io.BytesIO(file.read()))
                for _, row in df.iterrows():
                    if pd.isna(row.get('username')) or pd.isna(row.get('email')): continue
                    user, created = Faculty.objects.get_or_create(username=str(row['username']).strip().lower())
                    user.email = row.get('email')
                    user.school = row.get('school', 'MPSTME')
                    if created: user.set_password("password123")
                    user.is_staff = True
                    user.save()
                messages.success(request, "Faculty imported successfully.")
                return redirect("admin:booking_app_faculty_changelist")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return render(request, 'admin/bulk_upload.html', {'title': 'Bulk Upload Faculty'})


@admin.register(Examiner)
class ExaminerAdmin(admin.ModelAdmin):
    list_display = ('name', 'sap_vendor_code', 'mobile_number', 'upload_button')

    def upload_button(self, obj=None):
        url = reverse('admin:examiner_bulk_upload')
        return format_html(
            '<a class="button" style="background:#28a745; color:white; padding:5px 10px; border-radius:4px;" href="{}">Bulk Upload</a>',
            url)

    def get_urls(self):
        return [path('bulk-upload-examiner/', self.admin_site.admin_view(self.bulk_upload_examiner),
                     name='examiner_bulk_upload')] + super().get_urls()

    def bulk_upload_examiner(self, request):
        if request.method == "POST":
            file = request.FILES.get('excel_file')
            try:
                # Vercel fix: Read from memory
                df = pd.read_excel(io.BytesIO(file.read()))
                for _, row in df.iterrows():
                    sap_code = str(row.get('sap_vendor_code', '')).strip()
                    if not sap_code: continue
                    Examiner.objects.update_or_create(sap_vendor_code=sap_code,
                                                      defaults={'name': row['name'],
                                                                'mobile_number': row.get('mobile_number')})
                messages.success(request, "Supervisors imported.")
                return redirect("admin:booking_app_examiner_changelist")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return render(request, 'admin/bulk_upload.html', {'title': 'Bulk Upload Supervisor'})


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booked_by', 'examiner', 'school_name', 'date', 'slot', 'sms_status', 'is_paid', 'display_total_amount')

    def display_total_amount(self, obj):
        return obj.total_amount

    display_total_amount.short_description = "Total"

    def sms_status(self, obj):
        last_log = obj.sms_logs.order_by('-sent_at').first()
        if not last_log: return format_html('<span style="color: #999;">⚪ No Log</span>')
        color = "#28a745" if last_log.status == "Success" else "#dc3545"
        icon = "✔" if last_log.status == "Success" else "✘"
        return format_html(f'<span style="color: {color}; font-size: 1.2em;">{icon}</span>')

    sms_status.short_description = "SMS"

    # CRITICAL: This method must be inside the class and named exactly as called
    def _execute_sms_send(self, booking_obj, phone, message):
        url = "https://www.fast2sms.com/dev/bulkV2"
        # 1. Use os.environ.get for better Vercel reliability
        import os
        api_key = os.environ.get('FAST2SMS_KEY') 

        if not phone or not api_key:
            error = f"Fail: Phone={phone}, KeyFound={'Yes' if api_key else 'No'}"
            SMSLog.objects.create(booking=booking_obj, status="Failed", response_body=error)
            return

        # 2. Change to form-encoded payload for Fast2SMS compatibility
        payload = {
            "route": "q",
            "message": message,
            "language": "english",
            "numbers": str(phone),
        }
        
        headers = {
            "authorization": api_key,
            "Content-Type": "application/x-www-form-urlencoded", # Changed from JSON
            "Cache-Control": "no-cache"
        }

        try:
            # 3. Use 'data=' instead of 'json='
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            res_data = response.json()
            
            # 4. Success check
            status = "Success" if res_data.get("return") else "Failed"
            
            SMSLog.objects.create(
                booking=booking_obj,
                mobile_number=phone,
                status=status,
                response_body=str(res_data)
            )
        except Exception as e:
            SMSLog.objects.create(booking=booking_obj, status="Failed", response_body=str(e))



    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(booked_by=request.user)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.booking_dashboard), name='booking_dashboard'),
            path('bulk-enroll/', self.admin_site.admin_view(self.bulk_enroll_from_dashboard), name='bulk_enroll_slots'),
            path('supervisor-summary-report/', self.admin_site.admin_view(self.supervisor_summary_report),
                 name='supervisor_summary_report'),
            path('export-summary-excel/', self.admin_site.admin_view(self.export_summary_to_excel),
                 name='export_summary_excel'),
        ]
        return custom_urls + urls

    def bulk_enroll_from_dashboard(self, request):
        if request.method == "POST":
            selected_data = request.POST.getlist('selected_slots')
            enrolled_items = []
            batch_id = f"BATCH-{timezone.now().strftime('%y%m%d%H%M%S')}"

            try:
                with transaction.atomic():
                    for item in selected_data:
                        ex_id, d_str, s_val = item.split('|')
                        obj, created = Booking.objects.get_or_create(
                            examiner_id=ex_id, date=d_str, slot=s_val,
                            defaults={
                                'booked_by': request.user,
                                'is_paid': True,
                                'transaction_id': batch_id,
                                'school_name': request.user.school
                            }
                        )
                        if created:
                            enrolled_items.append({'obj': obj, 'date': d_str, 'slot': s_val})

                if enrolled_items:
                    grouped = defaultdict(list)
                    for item in enrolled_items:
                        grouped[item['obj'].examiner.id].append(item)

                    for ex_id, items in grouped.items():
                        first_item = items[0]['obj']
                        clean_phone = first_item.examiner.mobile_number  # Ensure this field exists
                        summary_list = [f"{i['date']}({i['slot']})" for i in items]
                        message = f"Dear {first_item.examiner.name}, confirmed for {first_item.school_name} on: {', '.join(summary_list)}."

                        # Correctly calling the method within the class
                        self._execute_sms_send(first_item, clean_phone, message)

                    messages.success(request, f"Successfully booked {len(enrolled_items)} slots.")
                return redirect(reverse('admin:booking_dashboard'))
            except Exception as e:
                messages.error(request, f"Error: {e}")
        return redirect(reverse('admin:booking_dashboard'))

    def booking_dashboard(self, request):
        date_str = request.GET.get('date')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        week_days = [start_of_week + timedelta(days=i) for i in range(7)]
        examiners = Examiner.objects.all()
        all_bookings = Booking.objects.filter(date__range=[week_days[0], week_days[-1]])
        for ex in examiners:
            ex.week_bookings = [b for b in all_bookings if b.examiner_id == ex.id]
        return render(request, 'admin/examiner/booking_dashboard.html', {
            **self.admin_site.each_context(request), 'examiners': examiners, 'selected_date': selected_date,
            'week_days': week_days, 'slots': [c[0] for c in Booking.SLOT_CHOICES]
        })

    def supervisor_summary_report(self, request):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        school_filter = request.GET.get('school')
        queryset = Booking.objects.all()
        if start_date_str and end_date_str:
            queryset = queryset.filter(date__range=[start_date_str, end_date_str])
        if school_filter:
            queryset = queryset.filter(school_name=school_filter)

        report_data = queryset.values(
            'school_name', 'examiner__sap_vendor_code', 'examiner__name', 'examiner__mobile_number'
        ).annotate(
            exam_count=Count('id')
        ).order_by('school_name', 'examiner__name')

        return render(request, 'admin/examiner/report.html', {
            **self.admin_site.each_context(request),
            'title': 'Supervisor Summary Report',
            'report_data': report_data,
            'school_choices': Faculty.SCHOOL_CHOICES,
        })

    def export_summary_to_excel(self, request):
        from openpyxl.styles import Font
        school_q = request.GET.get('school')
        start_d = request.GET.get('start_date')
        end_d = request.GET.get('end_date')

        queryset = Booking.objects.all()
        if school_q: queryset = queryset.filter(school_name=school_q)
        if start_d and end_d: queryset = queryset.filter(date__range=[start_d, end_d])

        report_data = queryset.values(
            'school_name', 'examiner__sap_vendor_code', 'examiner__name'
        ).annotate(exam_count=Count('id')).order_by('school_name', 'examiner__name')

        data = [{"SR.NO.": i + 1, "School": item['school_name'], "Code": item['examiner__sap_vendor_code'],
                 "Name": item['examiner__name'], "Exams": item['exam_count'], "Remuneration": item['exam_count'] * 300}
                for i, item in enumerate(report_data)]

        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=Report_{timezone.now().date()}.xlsx'

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, startrow=5, sheet_name='Summary')
            ws = writer.sheets['Summary']
            ws.cell(row=1, column=1, value="NMIMS EXAM PORTAL SUMMARY").font = Font(bold=True)
        return response


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('booking', 'mobile_number', 'status', 'sent_at')
    readonly_fields = ('booking', 'mobile_number', 'status', 'sent_at', 'response_body')

    def has_add_permission(self, request): return False
