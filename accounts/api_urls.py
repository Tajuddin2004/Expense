from django.urls import path
from . import api_views

urlpatterns = [
    path('csrf/', api_views.get_csrf_token, name='api_csrf'),
    path('signup/', api_views.signup_api, name='api_signup'),
    path('verify-otp/', api_views.verify_otp_api, name='api_verify_otp'),
    path('resend-otp/', api_views.resend_otp_api, name='api_resend_otp'),
    path('signin/', api_views.signin_api, name='api_signin'),
    path('signout/', api_views.signout_api, name='api_signout'),
    path('forgot-password/', api_views.forgot_password_api, name='api_forgot_password'),
    path('reset-password/', api_views.reset_password_api, name='api_reset_password'),
    path('user/', api_views.current_user_api, name='api_current_user'),
]
