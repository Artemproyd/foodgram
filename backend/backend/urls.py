from django.contrib import admin
from django.shortcuts import redirect, get_object_or_404
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.models import ShortLink


def ggg(request, short_link):
    full_url = str(request.build_absolute_uri())
    short_link_obj = get_object_or_404(ShortLink, short_url=short_link)
    url = full_url.replace(f'/s/{short_link}',
                           f':8000/{short_link_obj.original_url}')
    return redirect(str(url))


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_link>/', ggg, name='my_redirect')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
