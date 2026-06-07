from django.contrib import admin
from django.urls import path, include
from .diag import diag
from django.conf import settings
from django.conf.urls.static import static
from .views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="home"),
    path('auth/', include('Authentication.urls')),
    path('Calendar/', include('Calendar.urls')),
    path('Message/', include('Message.urls')),
    path('Weather/', include('Weather.urls')),
    path('Stocks/', include('Stocks.urls')),
    path('diag/', diag, name='diag'),
    path('Dashboard/', include(('Dashboard.urls', 'Dashboard'), namespace='Dashboard')),
    path('spotify/', include('spotify.urls')),
    path('LEDs/', include('LEDs.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

