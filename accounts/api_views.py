from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import EmailOTP
from .serializers import (
    SignUpSerializer, VerifyOTPSerializer, SignInSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, UserSerializer
)
from .views import send_otp_email


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    GET this endpoint first to ensure the CSRF cookie is set in the browser.
    Returns the token in JSON as well so decoupled frontends can use it.
    """
    from django.middleware.csrf import get_token
    token = get_token(request)
    return Response({"csrfToken": token, "detail": "CSRF cookie set."})


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_api(request):
    serializer = SignUpSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data['username']
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    name = serializer.validated_data.get('name', '').strip()

    first_name = name
    last_name = ''
    if ' ' in name:
        parts = name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1]

    # Delete any unverified user from previous attempts
    User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email), is_active=False).delete()

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=False
    )

    otp_obj = EmailOTP.generate_otp(user=user, purpose='signup')
    email_sent = send_otp_email(user, otp_obj.otp_code, "Account Registration")

    return Response({
        "success": True,
        "message": f"6-digit OTP code dispatched to {user.email}.",
        "email": user.email,
        "email_sent": email_sent
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_api(request):
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp_code'].strip()

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return Response({"error": "User with this email not found."}, status=status.HTTP_404_NOT_FOUND)

    otp_obj = EmailOTP.objects.filter(
        user=user,
        otp_code=otp_code,
        purpose='signup',
        is_used=False
    ).order_by('-created_at').first()

    if otp_obj and otp_obj.is_valid():
        otp_obj.is_used = True
        otp_obj.save()

        user.is_active = True
        user.save()

        login(request, user)
        return Response({
            "success": True,
            "message": "Account successfully verified and activated!",
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid or expired OTP code."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp_api(request):
    email = request.data.get('email', '').strip()
    user = User.objects.filter(email__iexact=email, is_active=False).first()
    if not user:
        return Response({"error": "No pending unverified account found for this email."}, status=status.HTTP_404_NOT_FOUND)

    otp_obj = EmailOTP.generate_otp(user=user, purpose='signup')
    email_sent = send_otp_email(user, otp_obj.otp_code, "Account Registration")
    return Response({
        "success": True,
        "message": f"A fresh OTP has been sent to {user.email}.",
        "email_sent": email_sent
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def signin_api(request):
    serializer = SignInSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username_or_email = serializer.validated_data['username_or_email'].strip()
    password = serializer.validated_data['password']

    # Resolve username from email if needed
    if '@' in username_or_email:
        user_obj = User.objects.filter(email__iexact=username_or_email).first()
        username = user_obj.username if user_obj else username_or_email
    else:
        username = username_or_email
        user_obj = User.objects.filter(username__iexact=username).first()
        # Use the canonical username casing Django stored, so authenticate() works
        if user_obj:
            username = user_obj.username

    if user_obj and not user_obj.is_active:
        # Resend OTP for unverified accounts
        otp_obj = EmailOTP.generate_otp(user=user_obj, purpose='signup')
        send_otp_email(user_obj, otp_obj.otp_code, "Account Verification")
        return Response({
            "error": "Account not verified yet. We have sent a new OTP to your email.",
            "unverified": True,
            "email": user_obj.email
        }, status=status.HTTP_403_FORBIDDEN)

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({
            "success": True,
            "message": f"Welcome back, {user.username}!",
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    else:
        # Helpful distinct errors: wrong password vs no account
        if user_obj:
            return Response({"error": "Incorrect password. Please try again."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"error": "No account found with that username or email."}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def signout_api(request):
    logout(request)
    return Response({"success": True, "message": "Signed out successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_api(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email'].strip()
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return Response({"error": "No account found with that email address."}, status=status.HTTP_404_NOT_FOUND)

    otp_obj = EmailOTP.generate_otp(user=user, purpose='reset')
    email_sent = send_otp_email(user, otp_obj.otp_code, "Password Reset")

    return Response({
        "success": True,
        "message": f"Password reset OTP sent to {user.email}.",
        "email": user.email,
        "email_sent": email_sent
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_api(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email'].strip()
    otp_code = serializer.validated_data['otp_code'].strip()
    new_password = serializer.validated_data['new_password']

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    otp_obj = EmailOTP.objects.filter(
        user=user,
        otp_code=otp_code,
        purpose='reset',
        is_used=False
    ).order_by('-created_at').first()

    if otp_obj and otp_obj.is_valid():
        otp_obj.is_used = True
        otp_obj.save()

        user.set_password(new_password)
        user.save()

        return Response({
            "success": True,
            "message": "Password reset successfully! You can now sign in with your new password."
        }, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid or expired OTP code."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def current_user_api(request):
    if request.user.is_authenticated:
        return Response({"authenticated": True, "user": UserSerializer(request.user).data})
    return Response({"authenticated": False, "user": None})
