from django.contrib import admin
from .models import Session, College, Department, Programme, Level, Semester, Student, Enrollment, Course, Registration, confirmRegister, Result, LevelAdvisor


def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == 'user':
        kwargs['queryset'] = CustomUser.objects.filter(stream='A')
    return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('year', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('year',)

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    search_fields = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'college')
    list_filter = ('college',)
    search_fields = ('name',)

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'duration', 'degree')
    list_filter = ('department',)
    search_fields = ('name',)

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    search_fields = ('name',)

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('surname', 'matricNumber', 'currentLevel', 'currentSession', 'student_status')
    list_filter = ('currentLevel', 'student_status', 'programme')
    search_fields = ('surname', 'matricNumber')
    list_select_related = ('currentLevel', 'currentSession', 'programme', 'department', 'college')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'enrolled_date')
    list_filter = ('session',)
    search_fields = ('student__surname', 'student__matricNumber')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('courseCode', 'title', 'unit', 'status', 'category', 'level', 'semester')
    list_filter = ('status', 'category', 'level', 'semester', 'department')
    search_fields = ('courseCode', 'title')
    filter_horizontal = ('programme',)

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'courseCode', 'session', 'semester', 'instructor_remark')
    list_filter = ('session', 'instructor_remark')
    search_fields = ('student__surname', 'student__matricNumber', 'courseCode')

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('registration', 'attempt_number', 'grade_type', 'grade_remark', 'passed', 'carried_over')
    list_filter = ('attempt_number', 'grade_type', 'grade_remark', 'passed', 'carried_over')
    search_fields = ('registration__student__surname', 'registration__student__matricNumber')

@admin.register(confirmRegister)
class ConfirmRegAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'semester', 'level', 'gpa', 'totalUnits')
    list_filter = ('session', 'gpa')
    search_fields = ('student__surname', 'student__matricNumber')

@admin.register(LevelAdvisor)
class LevelAdvisorAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'department', 'level', 'stream')
    list_filter = ('department', 'level')
    search_fields = ('name', 'departemt')