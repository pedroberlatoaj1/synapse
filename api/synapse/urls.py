"""Root URL configuration. Ninja routers wired in Bloco 3+."""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
