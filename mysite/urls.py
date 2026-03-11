from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("todo/", include("todo.urls")),
    path("", lambda request: redirect("todo:list")),
    path("", include("accounts.urls")),
    path("interaction/", include("interaction.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("reviews/", include("reviews.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
