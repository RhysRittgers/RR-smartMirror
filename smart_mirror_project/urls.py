"""
URL configuration for smart_mirror_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from .views import home
from .diag import diag
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('auth/', include('Authentication.urls')),
    path('Calendar/', include('Calendar.urls')), #syntax to connect calendar urls to main urls
    path('Message/', include('Message.urls')),
    path('Weather/', include('Weather.urls')),
    path('Stocks/', include('Stocks.urls')),
    path('diag/', diag, name='diag'),
    
    path('Dashboard/', include(('Dashboard.urls', 'Dashboard'), namespace='Dashboard')),

    path('spotify/', include('spotify.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
