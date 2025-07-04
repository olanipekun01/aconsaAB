"""aconsaAB URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve
from django.shortcuts import render


from django.conf.urls.static import static

from django.conf.urls import handler404

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_404_view

urlpatterns = [
    path('adminhddgdgdgdgdgdgddg/', admin.site.urls),
    path('', include('common.urls')),
    path('stream_a/', include('stream_a.urls')),
    path('stream_b/', include('stream_b.urls')),
    # Add instructor and advisor apps later if seperated

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

