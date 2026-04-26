"""Root URL configuration.

The Ninja API is mounted at /api/. Resource routers (decks, cards,
review, sync, stats) plug in over the next blocos.
"""
from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI

from apps.accounts.api import AuthController
from apps.decks.api import router as decks_router

api = NinjaExtraAPI(
    title="Synapse API",
    version="0.1.0",
    description="SRS for high-performance students. JWT Bearer auth.",
    docs_url="/docs",
)
api.register_controllers(AuthController)
api.add_router("/decks", decks_router)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
