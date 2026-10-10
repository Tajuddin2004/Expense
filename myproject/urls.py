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
import mimetypes
from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path, include, re_path
from expenses.views import custom_404_view


def serve_client(request, path="index.html"):
    if not path or path == "":
        path = "index.html"
    file_path = settings.BASE_DIR / "client" / path
    if file_path.is_file():
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if path.endswith(".css"):
            mime_type = "text/css"
        elif path.endswith(".js"):
            mime_type = "application/javascript"
        elif path.endswith(".html"):
            mime_type = "text/html"
        return FileResponse(open(file_path, "rb"), content_type=mime_type or "application/octet-stream")
    raise Http404("File not found")


urlpatterns = [
    path("admin/", admin.site.urls),
    # REST API Endpoints (Decoupled Server Backend)
    path("api/auth/", include("accounts.api_urls")),
    path("api/expenses/", include("expenses.api_urls")),

    # Client Application Routes: Root (/) and /client/ both serve the cinematic frontend
    path("", lambda r: serve_client(r, "index.html")),
    path("css/<path:path>", lambda r, path: serve_client(r, f"css/{path}")),
    path("js/<path:path>", lambda r, path: serve_client(r, f"js/{path}")),
    path("client/<path:path>", lambda r, path: serve_client(r, path)),
    path("client/", lambda r: serve_client(r, "index.html")),

    # Traditional Django server-rendered routes (for fallback)
    path("accounts/", include("accounts.urls")),
    path("expenses/", include("expenses.urls")),

    # Catch-all route: serves the custom 404 page for any invalid URL
    re_path(r"^.*$", custom_404_view),
]

# Custom 404 Error Handler (for DEBUG=False)
handler404 = 'expenses.views.custom_404_view'