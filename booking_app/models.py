from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime


class Faculty(AbstractUser):
    SCHOOL_CHOICES = [
        ('MPSTME', 'Mukesh Patel School of Technology Management & Engineering'),
        ('ASMSOC', 'Anil Surendra Modi School of Commerce'),
        ('SBM', 'School of Business Management'),
        ('SAMSOE', 'Sarla Anil Modi School of Economics'),
        ('SPPSPTM', 'Shobhaben Pratapbhai Patel School of Pharmacy & Technology Management'),
        ('KPMSOL', 'Kirit P. Mehta School of Law'),
        ('SDSOS', 'Sunandan Divatia School of Science'),
        ('SOD', 'School of Design'),
        ('SOHM', 'School of Hospitality Management'),
        ('SOMSR', 'School of Mathematical Sciences'),
        ('SOPC', 'School of Performing Arts'),
        ('STME', 'School of Technology Management & Engineering'),
    ]

    middle_name = models.CharField(max_length=100, null=True, blank=True)
    school = models.CharField(max_length=10, choices=SCHOOL_CHOICES, default='MPSTME')
    registered_date = models.DateTimeField(auto_now_add=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    def is_otp_valid(self):
        if not self.otp_created_at: return False
        return timezone.now() < self.otp_created_at + datetime.timedelta(minutes=5)

    class Meta:
        verbose_name = "ExamDept"
        verbose_name_plural = "ExamDept"


class Examiner(models.Model):
    name = models.CharField(max_length=255)
    sap_vendor_code = models.CharField(max_length=50, unique=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    creator = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)

    def get_clean_mobile(self):
        """Returns a 10-digit mobile number by removing +91 or 91 prefixes."""
        if not self.mobile_number:
            return None
        num = str(self.mobile_number).replace(" ", "").strip()
        if num.startswith('+91'):
            return num[3:]
        elif len(num) == 12 and num.startswith('91'):
            return num[2:]
        return num

    def __str__(self):
        return f"{self.name} ({self.sap_vendor_code})"


class Booking(models.Model):
    SCHOOL_CHOICES = Faculty.SCHOOL_CHOICES

    SLOT_CHOICES = [
        ('09:00-10:00', '09:00 AM - 10:00 AM'),
        ('10:00-11:00', '10:00 AM - 11:00 AM'),
        ('11:00-12:00', '11:00 AM - 12:00 PM'),
        ('12:00-13:00', '12:00 PM - 1:00 PM'),
        ('13:00-14:00', '01:00 PM - 02:00 PM'),
        ('14:00-15:00', '02:00 PM - 03:00 PM'),
        ('15:00-16:00', '03:00 PM - 04:00 PM'),
        ('16:00-17:00', '04:00 PM - 05:00 PM'),
    ]

    examiner = models.ForeignKey(Examiner, on_delete=models.CASCADE)
    date = models.DateField()
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    school_name = models.CharField(max_length=10, choices=SCHOOL_CHOICES, default='MPSTME')
    is_paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Transaction ID")
    num_supervision = models.PositiveIntegerField(default=1, verbose_name="No of supervision")
    rate_per_supervision = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                               verbose_name="Rate per supervision")
    booked_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=False,
                                  related_name='my_bookings')

    @property
    def total_amount(self):
        return self.num_supervision * self.rate_per_supervision

    def clean(self):
        # Validation for Transaction ID when marked as paid
        if self.is_paid and not self.transaction_id:
            raise ValidationError({'transaction_id': "Transaction ID is compulsory when 'Is Paid' is checked."})

        # Check for overlapping bookings
        overlap = Booking.objects.filter(examiner=self.examiner, date=self.date, slot=self.slot).exclude(pk=self.pk)
        if overlap.exists():
            existing = overlap.first()
            raise ValidationError(
                f"Conflict! This supervisor is already booked by {existing.get_school_name_display()} for this slot.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.examiner.name} | {self.date} | {self.slot}"


class SMSLog(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='sms_logs')
    mobile_number = models.CharField(max_length=15)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    response_body = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "SMS Log"
        verbose_name_plural = "SMS Logs"

    def __str__(self):
        return f"SMS to {self.mobile_number} - {self.status}"