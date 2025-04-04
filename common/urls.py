from django.urls import path, include
from . import views
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

app_name = 'common'

urlpatterns = [
    # Authentication
    # path('accounts/login/', views.login_view, name='login_view'),
    # path('accounts/logout/', views.logout, name='logout'),
    # path('success/', TemplateView.as_view(template_name='success.html'), name='success_page'),

    # # Parent views
    # path('check/result/filter/', views.ParentResultFilter, name='parent_result_filter'),
    # path('check/result/view/', views.ParentResultView, name='parent_result_view'),

    # # Instructor views (assuming they manage both streams)
    # path('instructor/dashboard/', views.adminDashboard, name='instructor_dashboard'),
    # path('instructor/programmes/', views.adminProgrammeManagement, name='instructor_programme_dashboard'),
    # path('instructor/programmes/delete/<str:id>/', views.deleteProgramme, name='instructor_delete_programme'),
    # path('instructor/programmes/upgrade/', views.UpdateProgramme, name='instructor_programme_update'),
    # path('instructor/programmes/<uuid:dept>/', views.adminProgrammeDepartmentManagement, name='instructor_programme_department_dashboard'),
    # path('instructor/studentlist/<uuid:dept>/<str:level>/', views.adminProgrammeDepartmentLevelManagement, name='instructor_programme_department_level_dashboard'),
    
    # path('instructor/departments/', views.adminDepartmentManagement, name='instructor_admin_department_management'),
    # path('instructor/departments/upgrade/', views.UpdateDepartment, name='instructor_update_department'),
    # path('instructor/departments/delete/<str:id>/', views.deleteDepartment, name='instructor_delete_department'),
    # path('instructor/departments/<uuid:dept>/', views.adminLevelDepartmentManagement, name='instructor_admin_level_department_management'),
    # path('instructor/student/list/<uuid:dept>/<str:level>/', views.adminStudentListDepartment, name='instructor_student_list_department'),
    
    # path('instructor/courses/', views.CourseDept, name='instructor_course_department'),
    # path('instructor/courses/<str:dept>/', views.adminCourseManagement, name='instructor_course_dashboard'),
    # path('instructor/courses/<str:dept>/update/', views.updateCourse, name='instructor_course_update'),
    # path('instructor/courses/delete/<str:dept>/<str:id>/', views.deleteCourse, name='instructor_delete_course'),
    # path('instructor/courses/each/<str:id>/', views.eachCourse, name='instructor_each_course'),
    # path('instructor/download/course-csv/', views.DownloadStudentCourse, name='instructor_course_student_download'),
    # path('instructor/upload/course-csv/', views.upload_csv, name='instructor_upload_csv'),
    
    # path('instructor/student/search/', views.registeredStudentSearchDashboard, name='instructor_student_search'),
    # path('instructor/student/management/', views.registeredStudentManagementDashboard, name='instructor_student_management'),
    # path('instructor/student/management/reg/delete/<str:id>/', views.deleteStudentRegisteredCourse, name='instructor_student_management_reg_delete'),
    # path('instructor/student/management/reg/add/<str:matricNo>/', views.addCourseStudentRegisteredCourse, name='instructor_student_management_reg_add'),
    # path('instructor/add_student/', views.manageAddStudent, name='instructor_manage_add_student'),
    # path('instructor/student/reg/<str:stats>/<str:id>/', views.ApproveRejectReg, name='instructor_approve_reject_reg'),
    # path('instructor/student/grade/', views.studentGradeUpdate, name='instructor_student_grade_update'),

    # # Advisor views (assuming they manage both streams)
    # path('advisor/dashboard/', views.AdvisorDashboard, name='advisor_dashboard'),
    # path('advisor/reg/', views.AdvisorReg, name='advisor_reg_matric'),
    # path('advisor/students/', views.StudentList, name='advisor_student'),
    # path('advisor/student/management/reg/delete/<str:id>/<str:matricNo>/', views.AdvisorDeleteStudentRegisteredCourse, name='advisor_student_management_reg_delete'),
    # path('advisor/student/management/reg/add/<str:matricNo>/', views.AdvisorAddCourseStudentRegisteredCourse, name='advisor_student_management_reg_add'),
    # path('advisor/student/reg/<str:stats>/<str:id>/<str:matricNo>/', views.AdvisorApproveRejectReg, name='advisor_approve_reject_reg'),
]