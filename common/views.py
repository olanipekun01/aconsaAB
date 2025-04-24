from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser, Instructor
from stream_a import models as ModelA
from stream_b import models as ModelB
from django.db.models import Q, F, OuterRef, Subquery, Max

from django.http import HttpResponse
from django.template.loader import render_to_string

from django.db.models import Sum, Min
import csv
from datetime import datetime
import os
import uuid
import random
import string
import json


def is_student(user):
    # print("User", User.role)
    return user.user_type == "student"
    # return True


def is_instructor(user):
    return user.user_type == "instructor"


def is_advisor(user):
    return user.user_type == "leveladvisor"



def loginView(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        
        try:
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                # Redirect based on user_type and stream
                if user.user_type == "student":
                    if user.stream == "a":
                        return redirect("stream_a:dashboard")
                    elif user.stream == "b":
                        return redirect("stream_b:dashboard")
                elif user.user_type == "instructor":
                    return redirect("/instructor/dashboard")  # Define this URL later
                elif user.user_type == "leveladvisor":
                    if user.stream == "a":
                        return redirect("stream_a:advisor_dashboard")
                    elif user.stream == "b":
                        return redirect("stream_b:advisor_dashboard")  # Define this URL later
                else:
                    messages.error(request, "Unknown user type.")
                    return redirect("/login/")
            else:
                messages.error(request, "Invalid credentials!")
                return redirect("/login/")
    
        except User.DoesNotExist:
            messages.info(request, f"Invalid credentials!")
            return redirect("/login/")

    return render(request, "common/login.html")

def logoutView(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("/login")


@login_required
@user_passes_test(is_student, login_url="/404")
def changePassword(request):
    if request.user.is_authenticated:
        user = request.user

        if request.method == "POST":
            old_password = request.POST["oldpassword"]
            new_password = request.POST["newpassword"]
            confirm_password = request.POST["newpassword"]

            if new_password != confirm_password:
                return render(
                    request, "user/changepassword.html", {"error": "Use same password"}
                )

            if len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, "common/change_password.html")

            user = request.user

            if user.check_password(old_password):
                user.set_password(new_password)
                user = auth.authenticate(username=user.username, password=new_password)
                auth.login(request, user)
                messages.success(request, "Password changed successfully!")
                
                if user.user_type == "student":
                    return redirect(f"stream_{user.stream}:change_password")
                elif user.user_type == "instructor":
                    return redirect("instructor_change_password") 
                elif user.user_type == "leveladvisor":
                    return redirect(f"stream_{user.stream}:level_advisor_change_password")
            else:
                messages.error(request, "Incorrect old password.")
                return render(request, "common/change_password.html", {"stream": user.stream})

        return render(request, "common/changepassword.html", {"stream": user.stream})

@login_required
def Redirect(request):
    if request.user.is_authenticated:
        user = request.user

        if user is not None:
            auth.login(request, user)
            # Redirect based on user_type and stream
            if user.user_type == "student":
                if user.stream == "a":
                    return redirect("stream_a:dashboard")
                elif user.stream == "b":
                    return redirect("stream_b:dashboard")
            elif user.user_type == "instructor":
                return redirect("/instructor/dashboard")  
            elif user.user_type == "leveladvisor":
                if user.stream == "a":
                    return redirect("stream_a:advisor_dashboard")
                elif user.stream == "b":
                    return redirect("stream_b:advisor_dashboard")
            else:
                messages.error(request, "Unknown user type.")
                return redirect("/login/")
        else:
            messages.error(request, "Invalid credentials!")
            return redirect("/login/")
    return render(request, "common/login.html")







# Instructor

@login_required
@user_passes_test(is_instructor, login_url="/404")
def adminDashboard(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB
        
        
        countProgrammes = len(
            Models.Programme.objects.all()
        )
        countCourses = len(Models.Course.objects.all())
        countLevels = len(Models.Level.objects.all())

    return render(
        request,
        "admin/admin_dashboard.html",
        {
            "countProgrammes": countProgrammes,
            "countCourses": countCourses,
            "countLevels": countLevels,
            "department": "ACONSA INSTRUCTOR",
            "stream": activeStream,
        },
    )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def adminProgrammeManagement(request):
    if request.user.is_authenticated:

        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB
        

        # programmes = Programme.objects.filter(department='ACONSA Instructor')
        programmes = Models.Programme.objects.all()
        # countCourses = len(Course.objects.filter(department='ACONSA Instructor'))
        if request.method == "POST":
            programme_name = request.POST["programme_name"]
            programme_duration = request.POST["programme_duration"]
            programme_degree = request.POST["programme_degree"]
            programme_dept = request.POST["programme_dept"]

            if (
                programme_name != ""
                and programme_duration != ""
                and programme_degree != ""
            ):
                try:
                    if Models.Programme.objects.all().filter(name=programme_name).exists():
                        messages.info(request, "Programme already exist!")
                        return redirect("/instructor/programmes")

                    programmeObjects = Models.Programme.objects.create(
                        name=programme_name,
                        department=get_object_or_404(Models.Department, id=programme_dept),
                        duration=programme_duration,
                        degree=programme_degree,
                    )
                    programmeObjects.save()
                    messages.info(request, "Programme Added!")
                    return redirect("/instructor/programmes")
                except:
                    messages.info(request, f"Programme not available")
                    return redirect("/instructor/programmes")
            else:
                messages.info(request, f"Fields cannot be empty")
                return redirect("/instructor/programmes")

        return render(
            request,
            "admin/admin_program_management.html",
            {
                "programmes": programmes,
                "department": "ACONSA Instructor",
                "allDepts":Models.Department.objects.all(),
                "stream": activeStream,
            },
        )

@login_required
@user_passes_test(is_instructor, login_url="/404")
def adminProgrammeDepartmentManagement(request, dept):
    if request.user.is_authenticated:

        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        programmes = Models.Programme.objects.all()

        prog = get_object_or_404(Models.Programme, id=dept)

        levels = Models.Level.objects.all()

        return render(
            request,
            "admin/admin_program_dept_management.html",
            {
                "programmes": programmes,
                "dept": dept,
                "levels": levels,
                "departs": prog.name,
                "stream": activeStream,
            },
        )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def adminProgrammeDepartmentLevelManagement(request, dept, level):
    if request.user.is_authenticated:

        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB

        
        programmes = Models.Programme.objects.all()

        students = Models.Student.objects.all().filter(
            programme=get_object_or_404(Models.Programme, id=dept),
            currentLevel=get_object_or_404(Models.Level, name=level),
        )

        prog = Models.Programme.objects.all().filter(id=dept).first()

        return render(
            request,
            "admin/level_student_list.html",
            {
                "programmes": programmes,
                "departs": prog.name,
                "studentlist": students,
                "level": level,
                "stream": activeStream,
            },
        )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def UpdateProgramme(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        if request.method == "POST":
            p_id = request.POST["programme_id"]
            p_name = request.POST["programme_name"].strip()
            p_duration = request.POST["programme_duration"].strip()
            p_degree = request.POST["programme_degree"].strip()
            p_dept = request.POST["programme_dept"].strip()

            if p_name != "" and p_duration != "" and p_degree != "":
                try:
                    programmes = Models.Programme.objects.filter(id=p_id)[0]
                    programmes.name = p_name
                    programmes.degree = p_degree
                    programmes.duration = p_duration
                    programmes.department = get_object_or_404(Models.Department, id=p_dept)
                    programmes.save()
                    messages.info(request, f"Programme Updated")
                    return redirect("/instructor/programmes")
                except:
                    messages.info(request, f"Programme not available")
                    return redirect("/instructor/programmes")
            messages.info(request, f"Fields cannot be empty")
            return redirect("/instructor/programmes")
        return redirect("/instructor/programmes")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def deleteProgramme(request, id):
    user = request.user
    instructor = get_object_or_404(Instructor, user=user)


    activeStream = instructor.preferred_stream
    if activeStream == "":
        messages.error(request, 'Stream is not set')
        redirect("/404")
    Models = ModelA if activeStream == "a" else ModelB

    try:
        program = Models.Programme.objects.filter(id=id)[0]
        print("1", program.name)
        if Models.Programme.objects.all().filter(id=id).exists():
            messages.info(request, f"{program.name} deleted successfully")
            program = Models.Programme.objects.filter(id=id).delete()

            return redirect("/instructor/programmes")
        messages.info(request, f"Programme not available")
        return redirect("/instructor/programmes")
    except:
        messages.info(request, f"Programme not available")
        return redirect("/instructor/programmes")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def adminDepartmentManagement(request):
    if request.user.is_authenticated:

        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        # programmes = Programme.objects.filter(department='ACONSA Instructor')
        departments = Models.Department.objects.all()
        # countCourses = len(Course.objects.filter(department='ACONSA Instructor'))
        if request.method == "POST":
            dept_name = request.POST["department_name"]

            if dept_name != "":
                try:
                    if Models.Department.objects.all().filter(name=dept_name).exists():
                        messages.info(request, "Department already exist!")
                        return redirect("/instructor/departments")

                    deptObjects = Models.Department.objects.create(
                        name=dept_name,
                        college=get_object_or_404(
                            Models.College, id="e3aba966-49f1-40b1-a07a-7a79e32aac5d"
                        ),
                    )
                    deptObjects.save()
                    messages.info(request, "Department Added!")
                    return redirect("/instructor/departments")
                except:
                    messages.info(request, f"Something went wrong")
                    return redirect("/instructor/departments")
            else:
                messages.info(request, f"Fields cannot be empty")
                return redirect("/instructor/departments")

        return render(
            request,
            "admin/admin_department_management.html",
            {
                "departments": departments,
                "stream": activeStream,
            },
        )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def UpdateDepartment(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB

        if request.method == "POST":
            dept_id = request.POST["department_id"]
            dept_name = request.POST["department_name"].strip()

            if dept_name != "":
                try:
                    department = Models.Department.objects.filter(id=dept_id)[0]
                    department.name = dept_name
                    department.save()
                    messages.info(request, f"Department Updated")
                    return redirect("/instructor/departments")
                except:
                    messages.info(request, f"Department not available")
                    return redirect("/instructor/departments")
            messages.info(request, f"Fields cannot be empty")
            return redirect("/instructor/departments")
        return redirect("/instructor/departments")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def deleteDepartment(request, id):
    user = request.user
    instructor = get_object_or_404(Instructor, user=user)

    activeStream = instructor.preferred_stream
    if activeStream == "":
        messages.error(request, 'Stream is not set')
        redirect("/404")
    Models = ModelA if activeStream == "a" else ModelB

    try:
        department = Models.Department.objects.filter(id=id)[0]
        print("1", department.name)
        if Models.Department.objects.all().filter(id=id).exists():
            messages.info(request, f"{department.name} deleted successfully")
            department = Models.Department.objects.filter(id=id).delete()

            return redirect("/instructor/departments")
        messages.info(request, f"Department not available")
        return redirect("/instructor/departments")
    except:
        messages.info(request, f"Department not available")
        return redirect("/instructor/departments")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def adminLevelDepartmentManagement(request, dept):
    if request.user.is_authenticated:

        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        programmes = Models.Programme.objects.all()

        department = get_object_or_404(Models.Department, id=dept)

        levels = Models.Level.objects.all()

        return render(
            request,
            "admin/admin_department_level.html",
            {
                "programmes": programmes,
                "dept": dept,
                "levels": levels,
                "departs": department.name,
                "stream": activeStream,
            },
        )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def adminStudentListDepartment(request, dept, level):
    if request.user.is_authenticated:

        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        programmes = Models.Programme.objects.all()

        students = Models.Student.objects.all().filter(
            department=get_object_or_404(Models.Department, id=dept),
            currentLevel=get_object_or_404(Models.Level, name=level),
        )

        dept = Models.Department.objects.all().filter(id=dept).first()

        return render(
            request,
            "admin/dept_level_student_list.html",
            {
                "programmes": programmes,
                "departs": dept.name,
                "studentlist": students,
                "level": level,
                "stream": activeStream,
            },
        )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def CourseDept(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB

        depts = Models.Department.objects.all()
        return render(
            request,
            "admin/course_dept.html",
            {"depts": depts, "department": "instructor", "stream": activeStream,},
        )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def adminCourseManagement(request, dept):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB

        # courses = Course.objects.all().filter(department='ACONSA Instructor')
        courses = [
            {
                "id": str(course.id),
                "title": course.title,
                "code": course.courseCode,
                "unit": course.unit,
                "status": course.status,
                "level": course.level.name,
                "semester": course.semester.name,
                "category": course.category,
                "programmes": [
                    str(prog_id)
                    for prog_id in course.programme.values_list("id", flat=True)
                ],  # Convert each programme ID to string
            }
            for course in Models.Course.objects.all().filter(
                department=get_object_or_404(Models.Department, id=dept)
            )
        ]
        # print('see courses', courses[0].title)
        cObjects = Models.Course.objects.all().filter(
            department=get_object_or_404(Models.Department, id=dept)
        )
        course_levels = []
        for x in cObjects:
            course_levels.append(x.level.name)
        course_levels.sort(key=str)
        course_levels = list(set(course_levels))
        print("course", course_levels)
        programmes = Models.Programme.objects.all().filter(
            department=get_object_or_404(Models.Department, id=dept)
        )
        # selected_programmes = courseObjects.programmes.all()
        if request.method == "POST":
            course_title = request.POST["course_title"].strip()
            course_code = request.POST["course_code"].strip()
            course_unit = request.POST["course_unit"].strip()
            course_status = request.POST["course_status"].strip()
            course_cat = request.POST["courseCat"]
            # program = request.POST['programme']
            level = request.POST["level"]
            semester = request.POST["semester"]

            if (
                course_title == ""
                and course_code == ""
                and course_unit == ""
                and course_status == ""
            ):
                messages.info(request, f"Fields cannot be empty")
                return redirect(f"/instructor/courses/{dept}")

            if Models.Course.objects.all().filter(courseCode=course_code).exists():
                messages.info(request, "Course already exist!")
                return redirect(f"/instructor/courses/{dept}")

            courseObjects = Models.Course.objects.create(
                title=course_title,
                courseCode=course_code,
                department='ACONSA Instructor',
                unit=course_unit,
                category=course_cat,
                status=course_status,
                level=get_object_or_404(Models.Level, name=level),
                semester=get_object_or_404(Models.Semester, name=semester),
            )

            courseObjects.save()
            programmes_ids = request.POST.getlist(
                "programmes"
            )  # Assuming departments are selected in a form

            programmes = Models.Programme.objects.filter(pk__in=programmes_ids)
            # Add all retrieved Programme instances to the courseObjects' programmes field
            courseObjects.programme.add(*programmes)
            messages.info(request, "Course Added!")
            return redirect(f"/instructor/courses/{dept}")

    return render(
        request,
        "admin/course_management.html",
        {
            "courses": courses,
            "courseLevels": course_levels,
            "programme": programmes,
            "department": "ACONSA Instructor",
            "deptid": dept,
            "streams": activeStream,
        },
    )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def updateCourse(request, dept):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        if request.method == "POST":
            course_id = request.POST["course_id"]
            course_title = request.POST["course_title"].strip()
            course_code = request.POST["course_code"].strip()
            course_unit = request.POST["course_unit"].strip()
            course_status = request.POST["course_status"].strip()
            course_cat = request.POST["courseCat"]
            level = request.POST["level"]
            semester = request.POST["semester"]
            # program = request.POST['programmes']

            if (
                course_title != ""
                and course_code != ""
                and course_unit != ""
                and course_status != ""
            ):
                try:
                    courseObjects = Models.Course.objects.filter(
                        department=get_object_or_404(Models.Department, id=dept), id=course_id
                    )[0]
                    courseObjects.title = course_title
                    courseObjects.courseCode = course_code
                    courseObjects.unit = course_unit
                    courseObjects.status = course_status
                    courseObjects.category = course_cat
                    courseObjects.level = get_object_or_404(Models.Level, name=level)
                    courseObjects.semester = get_object_or_404(Models.Semester, name=semester)
                    # courseObjects.programme = get_object_or_404(Programme, id=program)
                    courseObjects.save()
                    programmes_ids = request.POST.getlist(
                        "programmes"
                    )  # Assuming departments are selected in a form

                    programmes = Models.Programme.objects.filter(pk__in=programmes_ids)

                    # Add all retrieved Programme instances to the courseObjects' programmes field
                    courseObjects.programme.set(programmes)
                    messages.info(request, f"Course Updated")
                    return redirect(f"/instructor/courses/{dept}")
                except:
                    messages.info(request, f"Course not available")
                    return redirect(f"/instructor/courses/{dept}")
            messages.info(request, f"Fields cannot be empty")
            return redirect(f"/instructor/courses/{dept}")
        return redirect(f"/instructor/courses/{dept}")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def deleteCourse(request, dept, id):
    user = request.user
    instructor = get_object_or_404(Instructor, user=user)

    activeStream = instructor.preferred_stream
    if activeStream == "":
        messages.error(request, 'Stream is not set')
        redirect("/404")
    Models = ModelA if activeStream == "a" else ModelB

    try:
        courseObjects = Models.Course.objects.filter(
            department=get_object_or_404(Models.Department, id=dept), id=id
        )[0]
        print("1", courseObjects.title)
        if Models.Course.objects.all().filter(id=id).exists():
            messages.info(request, f"{courseObjects.title} deleted successfully")
            course = Models.Course.objects.filter(id=id).delete()

            return redirect(f"/instructor/courses/{dept}")
        messages.info(request, f"Course not available")
        return redirect(f"/instructor/courses/{dept}")
    except:
        messages.info(request, f"Course not available")
        return redirect(f"/instructor/courses/{dept}")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def eachCourse(request, id):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        session = Models.Session.objects.all()
        course = (
            Models.Course.objects.all().filter(id=id).first()
        )
        
        if request.method == "POST":
            sess = request.POST["session"]
            semes = request.POST["semester"]
            if sess != "" and semes != "":
                sess = get_object_or_404(Models.Session, year=sess)
                semes = get_object_or_404(Models.Semester, name=semes)

                register = Models.Registration.objects.all().filter(
                    session=sess,
                    semester=semes,
                    course=get_object_or_404(Models.Course, id=id),
                )
                

                return render(
                    request,
                    "admin/each_course.html",
                    {
                        "course": course,
                        "department": "ACONSA Instructor",
                        "session": session,
                        "registered_student": register,
                        "down_sess": sess,
                        "down_semes": semes,
                        "course_id": id,
                        "count": register.count(),
                        "stream": activeStream,
                    },
                )

            messages.info(request, f"Information not available")
            redirect(f"/instructor/courses/each/{id}/")
    return render(
        request,
        "admin/each_course.html",
        {"course": course, "department": 'ACONSA instructor', "session": session, "stream": activeStream},
    )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def DownloadStudentCourse(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB

        if request.method == "POST":
            id = request.POST["course_id"]
            sess = request.POST["session_year"]
            semes = request.POST["semester_name"]

            print('id', id)
            course = get_object_or_404(Models.Course, id=id)
            sess = get_object_or_404(Models.Session, year=sess)
            semes = get_object_or_404(Models.Semester, name=semes)
            registrations = Models.Registration.objects.filter(
                course=course, session=sess, semester=semes
            )

            # Create HTTP response with CSV content type
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="course_registration_{course.id}_{sess.year}.csv"'
            )

            # Create CSV writer
            writer = csv.writer(response)

            # Write header row
            writer.writerow(
                [
                    "Registration Id",
                    "Grade",
                    "Student Id",
                    "Matric No",
                    "Student Name",
                    "Course id",
                    "Course Code",
                    "Course Title",
                    "Session",
                    "Semester",
                    "Level",
                    "Total Units",
                ]
            )

            # Write data rows
            for registration in registrations:
                student = registration.student
                course = registration.course
                session = registration.session
                semester = registration.semester
                writer.writerow(
                    [
                        registration.id,
                        "",  # Leave grade blank for result upload
                        student.user.id,
                        student.matricNumber,
                        f"{student.otherNames} {student.surname}",
                        course.id,
                        course.courseCode,
                        course.title,
                        session.year,
                        semester.name,
                        course.level.name,
                        course.unit,
                    ]
                )

            return response


@login_required
@user_passes_test(is_instructor, login_url="/404")
def upload_csv(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB

        if request.method == "POST":

            course_id = request.POST["course_id"]
            if "uploadCsvFile" not in request.FILES:
                messages.error(
                    request, "No file uploaded. Please select a file and try again."
                )
                return redirect(f"/instructor/courses/each/{course_id}/")

            csv_file = request.FILES["uploadCsvFile"]
            session_year = request.POST["session_year"]
            semester_name = request.POST["semester_name"]

            current_session_model = Models.Session.objects.filter(is_current=True).first()
            current_semester_model = Models.Semester.objects.filter(is_current=True).first()

            # Check if the uploaded file is a CSV
            if not csv_file.name.endswith(".csv"):
                messages.error(request, "Please upload a valid CSV file.")
                return redirect(f"/instructor/courses/each/{course_id}/")

            if (
                get_object_or_404(Models.Session, year=session_year) == current_session_model
                and get_object_or_404(Models.Semester, name=semester_name)
                == current_semester_model
            ):

                try:
                    # Decode the file and process it
                    decoded_file = csv_file.read().decode("utf-8").splitlines()
                    reader = csv.reader(decoded_file)
                    next(reader, None)  # Skip the header row, if it exists

                    for row in reader:

                        print("row", row)
                        # try:
                        registration_id = row[0]
                        grade = row[1]

                        try:
                            # Convert string to UUID
                            reg_uuid = uuid.UUID(registration_id)
                            print(f"Converted UUID: {reg_uuid}")
                        except ValueError as e:
                            print(f"Invalid UUID string: {e}")

                        registration = Models.Registration.objects.filter(
                            id=uuid.UUID(registration_id)
                        ).first()

                        result = Models.Result.objects.filter(
                            registration__id=uuid.UUID(registration_id),
                            attempt_number=1,
                        ).first()

                        if result:
                            # If it exists, update the grade
                            result.grade = int(grade)  # Update the grade field
                            result.save()  # Save the changes
                            print("Existing result updated.")
                        else:
                            # If it doesn't exist, create a new result
                            result = Models.Result.objects.create(
                                registration=registration,
                                attempt_number=1,
                                grade=int(grade),
                            )
                            result.save()
                            print("New result created.")

                    messages.success(request, "CSV file processed successfully.")
                    return redirect(f"/instructor/courses/each/{course_id}/")

                except Models.Result.DoesNotExist:
                    messages.warning(
                        request, f"Registration ID {registration_id} does not exist."
                    )
                except IndexError:
                    messages.error(request, f"Invalid row format: {row}")
                except Exception as e:
                    messages.error(request, f"Error processing row {row}: {e}")

                return redirect(f"/instructor/courses/each/{course_id}/")
            else:
                messages.info(
                    request, f"Can only update current session and semester result!"
                )
                return redirect(f"/instructor/courses/each/{course_id}/")

        return redirect("/instructor/courses")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def registeredStudentSearchDashboard(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        session = Models.Session.objects.all()
        if request.method == "POST":
            matricNo = request.POST["matricNo"]
            sess = request.POST["session"]
            semes = request.POST["semester"]

            if sess != "" and semes != "" and matricNo != "":
                sess = get_object_or_404(Models.Session, year=sess)
                semes = get_object_or_404(Models.Semester, name=semes)
            messages.info(request, f"Fields cannot be empty!")
            redirect(f"instructor/student/search/")

    return render(
        request,
        "admin/student_management_search.html",
        {"department": "ACONSA Instructor", "session": session, "stream": activeStream},
    )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def registeredStuManagementDashboard(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        current_session = Models.Session.objects.filter(is_current=True).first()

        if request.method == "POST":
            matricNo = request.POST["matricNo"].strip()
            if matricNo != "":
                try:
                    student = Models.Student.objects.all().filter(
                        Q(matricNumber=matricNo) | Q(jambNumber=matricNo),
                    )
                    if student.exists():
                        stu = student.first()
                        registers = Models.Registration.objects.all().filter(
                            student=get_object_or_404(
                                Models.Student, matricNumber=stu.matricNumber
                            )
                        )
                        reg_levels = []
                        for x in registers:
                            reg_levels.append(x.level.name)
                        course_levels.sort(key=int)
                        course_levels = list(set(course_levels))

                        return render(
                            request,
                            "admin/student_dashboard.html",
                            {
                                "department": 'ACONSA Instructor',
                                "student": stu,
                                "registers": registers,
                                "stream": activeStream,
                            },
                        )
                except:
                    messages.info(request, f"Student not available")
                    return redirect("/instructor/student/management/")
            messages.info(request, f"Field cannot be empty!")
            redirect(f"/instructor/student/management/")

    return render(
        request,
        "admin/student_dashboard.html",
        {"department": "ACONSA Instructor", "curr_sess": current_session, "stream": activeStream},
    )


def F404(request):

    return render(request, "admin/404.html")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def registeredStudentManagementDashboard(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        current_session = Models.Session.objects.filter(is_current=True).first()
        current_semester = Models.Semester.objects.filter(is_current=True).first()
        if request.method == "POST":
            matricNo = request.POST["matricNo"].lower().strip()

            if matricNo != "":
                try:
                    student = (
                        Models.Student.objects.all()
                        .filter(
                            Q(matricNumber=matricNo) | Q(jambNumber=matricNo),
                        )
                        .first()
                    )

                    if student:

                        enrollment = (
                            Models.Enrollment.objects.filter(student=student)
                            .order_by("enrolled_date")
                            .first()
                        )

                        if not enrollment:
                            # Handle case where the student has no enrollment record
                            messages.info(request, f"No enrollment found!")
                            redirect(f"/instructor/student/management/")

                        enrollment_year = int(enrollment.session.year.split("/")[0])

                        # Query all registrations for the student and annotate each session with the calculated level
                        registrations = Models.Registration.objects.filter(
                            student=student
                        ).select_related("session")
                        # results = Result.objects.filter(student=student).select_related('registration__session')

                        # Calculate level for each session
                        sessions_and_levels = []
                        for registration in registrations:
                            res = (
                                Models.Result.objects.filter(registration__id=registration.id)
                                .order_by("-attempt_number")
                                .first()
                            )
                            session_year = int(registration.session.year.split("/")[0])
                            # Calculate the difference in years
                            years_since_enrollment = session_year - enrollment_year
                            # Calculate the level, assuming the student starts at Level 100 and progresses yearly
                            current_level = 100 + (years_since_enrollment * 100)

                            sessions_and_levels.append(
                                {
                                    "session": registration.session.year,
                                    "level": current_level,
                                    "registration": registration,  # Add any course details if necessary
                                    "result": res,
                                    "stream": activeStream,
                                }
                            )

                        unique_sessions = sorted(
                            {entry["session"] for entry in sessions_and_levels}
                        )

                        unique_levels = sorted(
                            {entry["level"] for entry in sessions_and_levels}
                        )

                        courses = Models.Course.objects.all()

                        duration = 0
                        if len(unique_levels) == len(unique_sessions):
                            duration = len(unique_levels)

                        context = {
                            "student": student,
                            "sessions_and_levels": sessions_and_levels,
                        }

                        return render(
                            request,
                            "admin/student_dashboard.html",
                            {
                                "department": "ACONSA Instructor",
                                "curr_sess": current_session,
                                "curr_semes": current_semester,
                                "student": student,
                                "sessions_and_levels": sessions_and_levels,
                                "unique_sessions": unique_sessions,
                                "unique_levels": unique_levels,
                                "duration": duration,
                                "courses": courses,
                                "matricNo": matricNo,
                                "stream": activeStream,
                            },
                        )
                    else:
                        messages.info(request, f"Student not registered!")
                        redirect(f"/instructor/student/management/")
                except Exception as e:
                    messages.info(request, f"Student not available {e}")
                    return redirect(f"/instructor/student/management/")
            else:
                messages.info(request, f"Field cannot be empty!")
                redirect(f"/instructor/student/management/")
    messages.info(request, f"Search for student above with matric No!")
    return render(
        request,
        "admin/student_dashboard.html",
        {
            "department": "ACONSA Instructor",
            "curr_sess": current_session,
            "curr_semes": current_semester,
            "stream": activeStream,
        },
    )


@login_required
@user_passes_test(is_instructor, login_url="/404")
def studentGradeUpdate(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        if request.method == "POST":
            registrationIdInput = request.POST["registrationIdInput"].strip()
            courseGrade = request.POST["course_grade"]

            # register = Registration.objects.all().filter(id=registrationIdInput).first()

            try:
                latest_result = (
                    Models.Result.objects.filter(registration__id=registrationIdInput)
                    .order_by("-attempt_number")
                    .first()
                )

                # Add a new result for the resit
                resit_result = Models.Result.objects.create(
                    registration=get_object_or_404(
                        Models.Registration, id=registrationIdInput
                    ),
                    attempt_number=latest_result.attempt_number + 1,
                    grade=float(courseGrade),  # Example resit grade
                )

                # register.grade = courseGrade
                # register.save()

                messages.info(
                    request, f"{latest_result.registration.course.title} grade updated!"
                )
                # requests.post('http://127.0.0.1:8000/target-endpoint/', data=data)
                redirect(f"/instructor/student/management/")
            except Exception as e:
                messages.info(request, f"result not uploaded yet")
                # requests.post('http://127.0.0.1:8000/target-endpoint/', data=data)
                redirect(f"/instructor/student/management/")

    return render(request, "admin/student_dashboard.html")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def deleteStudentRegisteredCourse(request, id):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        current_session_model = Models.Session.objects.filter(is_current=True).first()
        current_semester_model = Models.Semester.objects.filter(is_current=True).first()
    try:
        regObjects = Models.Registration.objects.filter(id=id)[0]
        print("1", regObjects.course.title)
        if (
            regObjects.session == current_session_model
            and regObjects.semester == current_semester_model
            and regObjects.instructor_remark != "approved"
        ):
            if Models.Registration.objects.all().filter(id=id).exists():
                messages.info(
                    request, f"{regObjects.course.title} deleted successfully"
                )
                regObjects = Models.Registration.objects.filter(id=id).delete()

                return redirect("/instructor/student/management/")
            messages.info(request, f"Registered Course not available")
            return redirect("/instructor/student/management/")
        messages.info(request, f"Cannot perform Opereation")
        return redirect("/instructor/student/management/")
    except:
        messages.info(request, f"Registered Course not available")
        return redirect("/instructor/student/management/")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def addCourseStudentRegisteredCourse(request, matricNo):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        try:
            student = (
                Models.Student.objects.all()
                .filter(
                    Q(matricNumber=matricNo) | Q(jambNumber=matricNo),
                    department='ACONSA Instructor',
                )
                .first()
            )
            if student:
                courseId = request.GET["course"]
                curr_semester = request.GET["curr_semester"]

                curr_session = request.GET["curr_session"]
                current_session_model = Models.Session.objects.filter(is_current=True).first()
                current_semester_model = Models.Semester.objects.filter(
                    is_current=True
                ).first()
                print(
                    "semester",
                    curr_semester,
                    current_semester_model,
                    type(curr_semester),
                    type(current_semester_model),
                    curr_semester == current_semester_model,
                )
                

                if (
                    curr_session == current_session_model.year
                    and curr_semester == current_semester_model.name
                ):
                    course = get_object_or_404(Models.Course, id=courseId)

                    if course.semester.name != current_semester_model.name:
                        messages.info(request, f"Invalid course to enter")
                        return redirect("/instructor/student/management/")

                    if (
                        Models.Registration.objects.all()
                        .filter(
                            student=student,
                            course=get_object_or_404(Course, id=courseId),
                            session=get_object_or_404(Session, year=curr_session),
                            semester=get_object_or_404(Semester, name=curr_semester),
                        )
                        .exists()
                    ):
                        messages.info(request, f"Already registered")
                        return redirect("/instructor/student/management/")

                    course_exist = Models.Registration.objects.create(
                        student=student,
                        course=get_object_or_404(Models.Course, id=courseId),
                        session=get_object_or_404(Models.Session, year=curr_session),
                        semester=get_object_or_404(Models.Semester, name=curr_semester),
                    )
                    course_exist.save()
                    messages.info(request, f"Course Updated")
                    return redirect("/instructor/student/management/")
                messages.info(request, f"Something went wrong!!")
                return redirect("/instructor/student/management/")
            messages.info(request, f"Student does not exist")
            return redirect("/instructor/student/management/")
        except:
            messages.info(request, f"Something went wrong")
            return redirect("/instructor/student/management/")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def ApproveRejectReg(request, stats, id):
    if request.user.is_authenticated:

        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        current_session_model = Models.Session.objects.filter(is_current=True).first()
        current_semester_model = Models.Semester.objects.filter(is_current=True).first()

        try:
            print(stats)
            if stats == "approved" or stats == "rejected":
                reg = Models.Registration.objects.filter(id=id).first()
                if (
                    reg.session == current_session_model
                    and reg.semester == current_semester_model
                ):
                    reg.instructor_remark = stats
                    reg.save()
                    messages.info(request, f"Registered Course {stats}!!")
                    return redirect("/instructor/student/management/")
                else:
                    messages.info(request, f"Request not allowed")
                    return redirect("/instructor/student/management/")
            else:
                messages.info(request, f"Invalid request")
                return redirect("/instructor/student/management/")
        except:
            messages.info(request, f"Registered Course not available")
            return redirect("/instructor/student/management/")
    return render(request, "admin/student_dashboard.html")


@login_required
@user_passes_test(is_instructor, login_url="/404")
def manageAddStudent(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB


        current_session_model = Models.Session.objects.filter(is_current=True).first()
        current_semester_model = Models.Semester.objects.filter(is_current=True).first()

        if request.method == "POST":
            file = request.FILES.get("file")

            if not file:
                messages.error(request, "Please upload a file.")
                return redirect("/instructor/add_student/")

            try:
                # Load file into a DataFrame (supports CSV/Excel)
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                elif file.name.endswith((".xls", ".xlsx")):
                    df = pd.read_excel(file)
                else:
                    messages.error(
                        request,
                        "Unsupported file format. Please upload a CSV or Excel file.",
                    )
                    return redirect("/instructor/add_student/")

                # Validate required columns
                required_columns = [
                    "surname",
                    "otherNames",
                    "currentLevel",
                    "entryLevel",
                    "matricNumber",
                    "jambNumber",
                    "dateOfBirth",
                    "gender",
                    "studentPhoneNumber",
                    "college",
                    "department",
                    "programme",
                    "primaryEmail",
                    "studentEmail",
                    "modeOfEntry",
                    "degree",
                    "currentSession",
                ]
                for column in required_columns:
                    if column not in df.columns:
                        messages.error(request, f"Missing required column: {column}")
                        return redirect("/instructor/add_student/")

                # Start a database transaction
                with transaction.atomic():
                    for _, row in df.iterrows():
                        # Fetch related foreign key objects
                        def safe_strip(value):
                            return str(value).strip() if isinstance(value, str) else str(value) if value is not None else ""
                        college = Models.College.objects.get(name=safe_strip(row['college']))
                        department = Models.Department.objects.get(name=safe_strip(row["department"]))
                        programme = Models.Programme.objects.get(name=safe_strip(row["programme"]))

                        

                        # Create a CustomUser (assuming email is primary key)
                        user, created = CustomUser.objects.update_or_create(
                            email=safe_strip(row["primaryEmail"]),
                            defaults={
                                "username": safe_strip(row["primaryEmail"]),
                                "first_name": safe_strip(row["otherNames"]),
                                "last_name": safe_strip(row["surname"]),
                                "user_type": "student",
                            },
                        )

                        user.set_password(safe_strip(row["surname"]).lower())
                        user.save()

                        # Create or update a Student record
                        student, created = Models.Student.objects.update_or_create(
                            user=user,
                            defaults={
                                "otherNames": safe_strip(row["otherNames"]),
                                "surname": safe_strip(row["surname"]),
                                "currentLevel": Models.Level.objects.get(name=safe_strip(row["currentLevel"])),
                                "entryLevel": Models.Level.objects.get(name=safe_strip(row["entryLevel"])),
                                "currentSession": current_session_model.year,
                                "matricNumber": safe_strip(row["matricNumber"]),
                                "jambNumber": safe_strip(row["jambNumber"]),
                                "dateOfBirth": datetime.strptime(
                                    safe_strip(row["dateOfBirth"]), "%m/%d/%Y"
                                ).strftime("%Y-%m-%d"),
                                "gender": safe_strip(row["gender"]),
                                "studentPhoneNumber": safe_strip(row["studentPhoneNumber"]),
                                "college": college,
                                "department": department,
                                "programme": programme,
                                "primaryEmail": safe_strip(row["primaryEmail"]),
                                "degree": safe_strip(row["degree"]),
                                "modeOfEntry": safe_strip(row["modeOfEntry"]),
                                "studentEmail": safe_strip(row["studentEmail"]),
                                "student_stream": "b",
                                "nationality": safe_strip(row["nationality"]),
                                "stateOfOrigin": safe_strip(row["stateOfOrigin"]),
                                "localGovtArea": safe_strip(row["localGovtArea"]),
                            },
                        )

                        

                    messages.success(request, "Students added successfully.")
                    return redirect("/instructor/add_student/")

            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect("/instructor/add_student/")

        return render(request, "admin/add_student.html", {"stream": activeStream})
    
@login_required
@user_passes_test(is_instructor, login_url="/404")
def switchStream(request):
    if request.user.is_authenticated:
        user = request.user
        instructor = get_object_or_404(Instructor, user=user)

        activeStream = instructor.preferred_stream
        if activeStream == "":
            messages.error(request, 'Stream is not set')
            redirect("/404")
        Models = ModelA if activeStream == "a" else ModelB

        if request.method == "POST" and "switch_stream" in request.POST:
            new_stream = request.POST.get("stream")
            if new_stream in ["a", "b"]:
                instructor.preferred_stream = new_stream
                instructor.save()
                stream = new_stream
                messages.success(request, f"Switched to Stream {new_stream.upper()}")
                return redirect("/instructor/dashboard/")
    
    return redirect("/instructor/dashboard/")