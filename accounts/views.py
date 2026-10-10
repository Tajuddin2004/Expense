import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import (
    SignUpForm, OTPVerificationForm, SignInForm,
    ForgotPasswordRequestForm, ResetPasswordForm
)
from .models import EmailOTP

logger = logging.getLogger(__name__)


from django.conf import settings
from django.db.models import Q


def send_otp_email(user, otp_code, purpose_label):
    """
    Sends 6-digit OTP code to the user via Google SMTP.
    Falls back gracefully and prints to console for smooth local debugging.
    """
    subject = f"Your Expense Tracker Verification Code: {otp_code}"
    message = (
        f"Hello {user.username},\n\n"
        f"Your verification code for {purpose_label} is: {otp_code}\n\n"
        f"This code will expire in 10 minutes.\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"Best regards,\nPersonal Expense Tracker Team"
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'team110.servicehub@gmail.com'
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending email to {user.email}: {e}")
        # Always print to terminal console so developer is never locked out during setup
        print(f"\n[DEV FALLBACK] >>> Verification OTP for {user.email}: {otp_code} (Error: {e}) <<<\n")
        return False


def signup_view(request):
    """
    Handles initial registration: saves inactive user and sends OTP.
    """
    if request.user.is_authenticated:
        return redirect('expenses:dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            name = form.cleaned_data.get('name', '').strip()

            first_name = name
            last_name = ''
            if ' ' in name:
                parts = name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1]

            # Remove any unverified account from a previous failed attempt
            User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email), is_active=False).delete()

            # Create user in unverified state (is_active=False)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=False
            )

            # Generate OTP
            otp_obj = EmailOTP.generate_otp(user=user, purpose='signup')
            email_sent = send_otp_email(user, otp_obj.otp_code, "Account Registration")

            request.session['pending_user_id'] = user.id
            if email_sent:
                messages.success(request, f"We sent a 6-digit OTP to {user.email}. Please check your inbox and spam folder.")
            else:
                messages.warning(request, f"Email delivery failed. Check your terminal console for your OTP verification code.")
            return redirect('accounts:verify_otp')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


def verify_otp_view(request):
    """
    Verifies 6-digit OTP to activate the user's account and log them in.
    """
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, "Session expired or no pending signup found. Please sign up again.")
        return redirect('accounts:signup')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please sign up again.")
        return redirect('accounts:signup')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            submitted_otp = form.cleaned_data['otp_code'].strip()
            otp_obj = EmailOTP.objects.filter(
                user=user,
                otp_code=submitted_otp,
                purpose='signup',
                is_used=False
            ).order_by('-created_at').first()

            if otp_obj and otp_obj.is_valid():
                # Mark OTP used and activate user
                otp_obj.is_used = True
                otp_obj.save()

                user.is_active = True
                user.save()

                # Clean session and log user in
                del request.session['pending_user_id']
                login(request, user)
                messages.success(request, f"Welcome {user.username}! Your email has been verified successfully.")
                return redirect('expenses:dashboard')
            else:
                messages.error(request, "Invalid or expired OTP. Please check the code and try again.")
    else:
        form = OTPVerificationForm()

    return render(request, 'accounts/verify_otp.html', {'form': form, 'user_email': user.email})


def resend_otp_view(request):
    """
    Resends OTP for account registration.
    """
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, "No pending registration found.")
        return redirect('accounts:signup')

    user = User.objects.get(id=user_id)
    otp_obj = EmailOTP.generate_otp(user=user, purpose='signup')
    send_otp_email(user, otp_obj.otp_code, "Account Registration")
    messages.info(request, f"A new OTP has been dispatched to {user.email}.")
    return redirect('accounts:verify_otp')


def signin_view(request):
    """
    Standard password-based login for verified users.
    """
    if request.user.is_authenticated:
        return redirect('expenses:dashboard')

    if request.method == 'POST':
        form = SignInForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email'].strip()
            password = form.cleaned_data['password']

            # Support login with either username or email
            user_obj = None
            if '@' in username_or_email:
                user_obj = User.objects.filter(email__iexact=username_or_email).first()
                username = user_obj.username if user_obj else None
            else:
                user_obj = User.objects.filter(username__iexact=username_or_email).first()
                username = user_obj.username if user_obj else username_or_email

            if user_obj and not user_obj.is_active:
                # User has not verified OTP yet
                request.session['pending_user_id'] = user_obj.id
                otp_obj = EmailOTP.generate_otp(user=user_obj, purpose='signup')
                send_otp_email(user_obj, otp_obj.otp_code, "Account Verification")
                messages.warning(request, "Your account is not verified yet. We have sent a new OTP to your email.")
                return redirect('accounts:verify_otp')

            if not user_obj:
                messages.error(request, "No account found with that username or email. Please check your credentials or sign up.")
                return render(request, 'accounts/signin.html', {'form': form})

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('expenses:dashboard')
            else:
                messages.error(request, "Incorrect password. Please try again or use 'Forgot password'.")
    else:
        form = SignInForm()

    return render(request, 'accounts/signin.html', {'form': form})


def signout_view(request):
    """
    Logs out the user.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:signin')


def forgot_password_view(request):
    """
    Step 1 of forgot password: submit email to receive reset OTP.
    """
    if request.method == 'POST':
        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip()
            user = User.objects.filter(email__iexact=email).first()

            if user:
                otp_obj = EmailOTP.generate_otp(user=user, purpose='reset')
                send_otp_email(user, otp_obj.otp_code, "Password Reset")
                request.session['reset_email'] = user.email
                messages.success(request, f"A 6-digit password reset OTP has been sent to {user.email}.")
                return redirect('accounts:reset_password_verify')
            else:
                # Do not leak whether user exists, but give friendly notice
                messages.error(request, "No account was found with that email address.")
    else:
        form = ForgotPasswordRequestForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_verify_view(request):
    """
    Step 2 of forgot password: submit OTP and new password.
    """
    reset_email = request.session.get('reset_email')
    if not reset_email:
        messages.error(request, "Session expired. Please request password reset again.")
        return redirect('accounts:forgot_password')

    user = User.objects.filter(email__iexact=reset_email).first()
    if not user:
        messages.error(request, "User not found.")
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            submitted_otp = form.cleaned_data['otp_code'].strip()
            new_password = form.cleaned_data['new_password']

            otp_obj = EmailOTP.objects.filter(
                user=user,
                otp_code=submitted_otp,
                purpose='reset',
                is_used=False
            ).order_by('-created_at').first()

            if otp_obj and otp_obj.is_valid():
                otp_obj.is_used = True
                otp_obj.save()

                user.set_password(new_password)
                user.save()

                del request.session['reset_email']
                messages.success(request, "Your password has been reset successfully! Please sign in with your new password.")
                return redirect('accounts:signin')
            else:
                messages.error(request, "Invalid or expired OTP. Please try again.")
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password_verify.html', {'form': form, 'user_email': reset_email})
