from django.urls import path
from . import views

from django.urls import re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls import handler404
from django.shortcuts import render

app_name = 'stream_b'

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

# Set the handler for 404 errors
handler404 = custom_404_view

urlpatterns = [
    path('', views.Dashboard, name='dashboard'),
    path('courses/', views.Courses, name='courses'),
    path('course/delete/<str:id>/', views.CourseDelete, name='course_delete'),
    path('result/filter/', views.ResultFilter, name='result_filter'),
    path('result/view/', views.ResultView, name='result_view'),
    path('print/', views.printCopy, name='print_copy'),
    # path('contact/', views.Contact, name='contact'),
    # path('accounts/changepassword/', views.changePassword, name='change_password'),
    path('profile/', views.Profile, name='profile'),
    
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    # path('404', views.F404, name='f404')
] 


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, 
                          document_root=settings.MEDIA_ROOT)