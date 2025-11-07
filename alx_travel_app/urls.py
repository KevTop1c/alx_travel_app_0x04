"""
URL configuration for alx_travel_app project.
"""

from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
# from django.views.generic import RedirectView
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

SchemaView = get_schema_view(
    openapi.Info(
        title="ALX Travel App API",
        default_version="v1",
        description="API Documentation for ALX Travel App",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@alxtravel.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)


# pylint: disable=unused-argument
@api_view(["GET"])
def home_view(request):
    """API Home/Welcome endpoint"""
    return Response(
        {
            "message": "Welcome to ALX Travel API",
            "version": "1.0",
            "endpoints": {
                "bookings": "/api/bookings/",
                "properties": "/api/properties/",
                "register": "/api/register/",
                "swagger": "/swagger/",
                "admin": "/admin/",
            },
        }
    )


urlpatterns = [
    path("", home_view, name="home"),
    # path("", RedirectView.as_view(url="swagger", permanent=False), name="home"),
    # Admin
    path("admin/", admin.site.urls),
    # API endpoint
    path("api/", include("listings.urls")),
    # Swagger UI
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        SchemaView.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        SchemaView.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", SchemaView.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # API root - browsable API
    path("api-auth/", include("rest_framework.urls")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
