import secrets
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailOTP(models.Model):
    PURPOSE_CHOICES = [
        ('signup', 'Sign Up Verification'),
        ('reset', 'Password Reset'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @classmethod
    def generate_otp(cls, user, purpose):
        # Generate cryptographically secure 6-digit numeric OTP
        code = f"{secrets.randbelow(900000) + 100000}"
        return cls.objects.create(user=user, otp_code=code, purpose=purpose)

    def is_valid(self):
        # Valid for 10 minutes and not used
        expiry_time = self.created_at + timedelta(minutes=10)
        return not self.is_used and timezone.now() <= expiry_time

    def __str__(self):
        return f"OTP for {self.user.email} ({self.purpose})"
