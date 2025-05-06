from django.urls import path, include
from . import views
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from django.urls import re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls import handler404
from django.shortcuts import render

app_name = "common"

# Define the custom 404 view
def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

# Set the handler for 404 errors
handler404 = custom_404_view

urlpatterns = [
    path("", views.Redirect, name="redirect"),
    path("login/", views.loginView, name="login"),
    path("logout/", views.logoutView, name="logout"),
    path("change-password/", views.changePassword, name="change_password"),


    # Instructor
    path('instructor/dashboard/', views.adminDashboard, name='instructor_dashboard'),
    path('instructor/programmes/', views.adminProgrammeManagement, name='instructor_programme_dashboard'),
    path('instructor/programmes/delete/<str:id>/', views.deleteProgramme, name='instructor_delete_programme'),
    path('instructor/programmes/upgrade/', views.UpdateProgramme, name='instructor_programme_update'),
    path('instructor/programmes/<uuid:dept>/', views.adminProgrammeDepartmentManagement, name='instructor_programme_department_dashboard'),
    path('instructor/studentlist/<uuid:dept>/<str:level>/', views.adminProgrammeDepartmentLevelManagement, name='instructor_programme_department_level_dashboard'),


    path('instructor/departments/', views.adminDepartmentManagement, name="instructorAdminDepartmentManagement"),
    path('instructor/departments/upgrade/', views.UpdateDepartment, name="instructorUpdateProgramme"),
    path('instructor/departments/delete/<str:id>/', views.deleteDepartment, name='instructordeleteDepartment'),
    path('instructor/departments/<uuid:dept>/', views.adminLevelDepartmentManagement, name='instructoradminLevelDepartmentManagement'),
    path('instructor/student/list/<uuid:dept>/<str:level>/', views.adminStudentListDepartment, name='adminStudentListDepartment'),


    path('instructor/courses/', views.CourseDept, name='instructor_course_department'),
    path('instructor/courses/<str:dept>/', views.adminCourseManagement, name='instructor_course_dashboard'),
    path('instructor/courses/<str:dept>/update/', views.updateCourse, name='instructor_course_update'),
    path('instructor/courses/delete/<str:dept>/<str:id>/', views.deleteCourse, name='instructor_delete_course'),
    path('instructor/courses/each/<str:id>/', views.eachCourse, name='instructor_each_course'),
    path('instructor/download/course-csv/', views.DownloadStudentCourse, name='instructor_course_student_download'),
    path('instructor/upload/course-csv/', views.upload_csv, name='upload_csv'),

    path('instructor/student/search/', views.registeredStudentSearchDashboard, name='instructor_student_search'),
    path('instructor/student/management/', views.registeredStudentManagementDashboard, name='instructor_student_management'),
    path('instructor/student/management/reg/delete/<str:id>/', views.deleteStudentRegisteredCourse, name='instructor_student_management_reg_delete'),
    path('instructor/student/management/reg/add/<str:matricNo>/', views.addCourseStudentRegisteredCourse, name='instructor_student_management_reg_add'),

    path('instructor/add_student/', views.manageAddStudent, name='manage_add_student'),

    path('instructor/student/reg/<str:stats>/<str:id>/', views.ApproveRejectReg, name='approve_reject_reg'),
    
    path('instructor/student/grade/', views.studentGradeUpdate, name='instructor_student_grade_update'),

    path('instructor/switch/stream/', views.switchStream, name='switch_stream'),
    
    
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    # path('404', views.F404, name='f404')
] 


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, 
                          document_root=settings.MEDIA_ROOT)