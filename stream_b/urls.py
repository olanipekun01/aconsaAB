from django.urls import path
from . import views

app_name = 'stream_b'

urlpatterns = [
    path('', views.Dashboard, name='dashboard'),
    # path('courses/', views.Courses, name='courses'),
    # path('course/delete/<str:id>/', views.CourseDelete, name='course_delete'),
    # path('result/filter/', views.ResultFilter, name='result_filter'),
    # path('result/view/', views.ResultView, name='result_view'),
    # path('print/', views.printCopy, name='print_copy'),
    # path('contact/', views.Contact, name='contact'),
    # path('accounts/changepassword/', views.changePassword, name='change_password'),
    # path('profile/', views.Profile, name='profile'),
]