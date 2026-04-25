"""Root URL configuration.

The Ninja API is mounted at /api/. Resource routers (decks, cards,
review, sync, stats) plug in over the next blocos.
"""
from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI

from apps.accounts.api import AuthController

api = NinjaExtraAPI(
    title="Synapse API",
    version="0.1.0",
    description="SRS for high-performance students. JWT Bearer auth.",
    docs_url="/docs",
)
api.register_controllers(AuthController)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
