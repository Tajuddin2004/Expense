"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from expenses.views import custom_404_view

urlpatterns = [
    path("admin/", admin.site.urls),
    # REST API Endpoints (Decoupled Server Backend)
    path("api/auth/", include("accounts.api_urls")),
    path("api/expenses/", include("expenses.api_urls")),

    # Client Application Route
    path("client/<path:path>", serve, {"document_root": settings.BASE_DIR / "client"}),
    path("client/", serve, {"document_root": settings.BASE_DIR / "client", "path": "index.html"}),

    path("accounts/", include("accounts.urls")),
    path("", include("expenses.urls")),
    # Catch-all route: serves the custom 404 page for any invalid URL even during DEBUG=True
    re_path(r"^.*$", custom_404_view),
]

# Custom 404 Error Handler (for DEBUG=False)
handler404 = 'expenses.views.custom_404_view'