from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from api.views import RecipeShortLinkRedirectView


urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        's/<str:short_id>/',
        RecipeShortLinkRedirectView.as_view(),
        name='short_link_redirect'
    ),

    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include('api.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
