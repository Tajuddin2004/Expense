from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import EmailOTP
from expenses.models import Expense


class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 0
    fields = ('title', 'amount', 'category', 'date')
    show_change_link = True


class EmailOTPInline(admin.TabularInline):
    model = EmailOTP
    extra = 0
    fields = ('otp_code', 'purpose', 'is_used', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False


# Re-register UserAdmin with Expense and OTP inlines for full administrator control
class UserAdmin(BaseUserAdmin):
    inlines = [ExpenseInline, EmailOTPInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'purpose', 'is_used', 'created_at')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('user__username', 'user__email', 'otp_code')
    readonly_fields = ('created_at',)
