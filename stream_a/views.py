import csv
import json
import os
import random
import string
import uuid
from datetime import datetime
from functools import reduce

import pandas as pd
import fpdf
from fpdf import FPDF, HTMLMixin

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User, auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import (
    Max, Q, F, Sum, Min, OuterRef, Subquery
)

from operator import or_
from functools import reduce

from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from urllib.parse import urlencode

from .models import *

from common.utils import *

UserModel = get_user_model()


# Role check for students
def is_student(user):
    return user.is_authenticated and user.user_type == "student"

def is_advisor(user):
    return user.user_type == "leveladvisor"


@login_required
@user_passes_test(is_student, login_url="/404")
def Dashboard(request):
    user = request.user
    
    # Check if the user belongs to Stream A
    if user.stream != "a":
        # Redirect to the correct stream's dashboard
        if user.stream == "b":
            messages.info(request, "You have been redirected to your Stream B dashboard.")
            return redirect("stream_b:dashboard")
        else:
            messages.error(request, "Invalid stream for this user.")
            return redirect("/login/")  # Fallback if stream is invalid

    # Fetch Stream A-specific student data
    student = get_object_or_404(Student, user=user)
    level = get_object_or_404(Level, name=student.currentLevel)
    current_session_model = Session.objects.filter(is_current=True).first()
    current_semester_model = Semester.objects.filter(is_current=True).first()

    if request.method == "POST":
        template = request.POST["template"]
        # Add any POST handling logic here if needed

    return render(request, "user/dashboard.html", {"student": student, "stream": user.stream})

def has_prerequisites_passed(student, course, checked_courses=None):
    """Recursively check if all prerequisites for a course are passed."""
    if checked_courses is None:
        checked_courses = set()
    if course.id in checked_courses:
        return True
    checked_courses.add(course.id)

    prereqs = course.prerequisites.all()
    if not prereqs:
        print(f"No prerequisites for course: {course.title}")
        return True

    for prereq in prereqs:
        has_passed = Result.objects.filter(
            registration__student=student,
            registration__course=prereq,
            grade_remark="passed"
        ).exists()
        if not has_passed or not has_prerequisites_passed(student, prereq, checked_courses):
            return False
    return True

def get_dependent_courses(course, all_courses, dependents=None):
    """Recursively find all courses that depend on the given course."""
    if dependents is None:
        dependents = set()
    for c in all_courses:
        if course in c.prerequisites.all() and c.id not in dependents:
            dependents.add(c.id)
            get_dependent_courses(c, all_courses, dependents)
    return dependents

@login_required
@user_passes_test(is_student, login_url="/404")
def Courses(request):
    if request.user.is_authenticated:
        user = request.user

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")  # Fallback if stream is invalid

        student = get_object_or_404(Student, user=user)

        level = get_object_or_404(Level, name=student.currentLevel)
        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()

        if request.method == "POST":
            courses = request.POST.getlist("courses")
            totalUnit = request.POST["totalUnit"]
            new_courses = Course.objects.filter(id__in=courses)
            new_units = new_courses.aggregate(total_units=Sum("unit"))["total_units"] or 0

           

            # Check prerequisites and register carryovers
            for course in new_courses:
                if not has_prerequisites_passed(student, course):
                    missing_prereqs = [
                        prereq.title for prereq in course.prerequisites.all()
                        if not Result.objects.filter(
                            registration__student=student,
                            registration__course=prereq,
                            grade_remark="passed"
                        ).exists()
                    ]
                    if course.status == "compulsory":
                        Registration.objects.get_or_create(
                            student=student,
                            course=course,
                            session=current_session_model,
                            semester=current_semester_model,
                            defaults={"instructor_remark": "pending"}
                        )
                    messages.error(
                        request,
                        f"Cannot register {course.title}: Missing prerequisites: {', '.join(missing_prereqs)}."
                    )
                    return redirect("stream_a:courses")



            # Filter registrations for the student, session, and semester
            registrations = Registration.objects.filter(
                student=student,
                session=current_session_model,
                semester=current_semester_model,
                instructor_remark__in=["approved", "pending"]
            )

            

            # Aggregate the total units by summing the 'unit' field of related courses
            total_units = registrations.aggregate(total_units=Sum("course__unit"))[
                "total_units"
            ]

            # Handle the case where no registrations exist
            total_units = total_units or 0

            total_units = total_units + new_units

            if total_units <= 30:
                for id in courses:

                    course = get_object_or_404(Course, id=id)
                    # Ensure course isn't already registered
                    if not registrations.filter(course=course).exists():
                        Registration.objects.create(
                            student=student,
                            course=course,
                            session=current_session_model,
                            semester=current_semester_model,
                            instructor_remark="pending"
                        )

                

                confirm_reg, created = confirmRegister.objects.get_or_create(
                    student=student,
                    session=current_session_model,
                    semester=current_semester_model,
                    level=get_object_or_404(Level, name=student.currentLevel),
                )

                if not created:
                    # Update the total units and registration date if the instance already exists
                    confirm_reg.totalUnits = total_units
                    confirm_reg.registration_date = now().date()
                    confirm_reg.save()
                else:
                    # If a new instance was created, set the totalUnits and save
                    confirm_reg.totalUnits = total_units
                    confirm_reg.save()
                messages.info(request, "Course added successfully.")
                return redirect("stream_a:courses")
            messages.error(request, "Exceeded maximum units (30).")
            return redirect("stream_a:courses")

        
        try:
            current_semester_model = Semester.objects.get(is_current=True)
        except ObjectDoesNotExist:
            # raise ValueError("No current semester is set. Please set one as current.")
            messages.error(
                request, "No current semester is set. Please set one as current."
            )
            return redirect("stream_a:courses")

        # Get the current session
        try:
            current_session_model = Session.objects.get(is_current=True)
        except ObjectDoesNotExist:
            messages.error(
                request, "No current session is set. Please set one as current."
            )
            return redirect("stream_a:courses")

        courses = Course.objects.filter(
            level=level,
            programme=student.programme,
            semester=current_semester_model,
        )

        registered_courses = Registration.objects.filter(
            student=student,
            semester=current_semester_model,
            session=current_session_model,  # Ensure this is the current academic session
            instructor_remark__in=["approved", "pending"],
        ).values_list("course_id", flat=True)
        
        previously_registered_courses = Registration.objects.filter(
            student=student
        ).values_list("course_id", flat=True)


        courses = courses.exclude(id__in=registered_courses).exclude(
            id__in=previously_registered_courses
        )

        available_courses = [
            course for course in courses if has_prerequisites_passed(student, course)
        ]
        unavailable_courses = [
            course for course in courses if not has_prerequisites_passed(student, course)
        ]

        


        #carry over logic

        # Step 1: Verify latest attempts
        latest_attempts = (
            Result.objects.filter(registration__student=student)
            .values("registration_id")
            .annotate(highest_attempt=Max("attempt_number"))
        )
        

        # Step 2: Construct the query for failed results
        conditions = [
            Q(
                registration_id=attempt["registration_id"],
                attempt_number=attempt["highest_attempt"],
            )
            for attempt in latest_attempts
        ]

        failed_results = Result.objects.filter(
            reduce(or_, conditions) if conditions else Q(),
            grade_remark__in=["failed", "pending"]
        ) if conditions else Result.objects.none()

        failed_registration_ids = list(failed_results.values_list("registration_id", flat=True))


        # Step 1: Filter all registrations for the student
        registrations = Registration.objects.filter(student=student)

        # Step 2: Identify courses registered in the current session
        courses_in_current_session = registrations.filter(
            session=current_session_model,
            semester=current_semester_model,
            instructor_remark__in=["approved", "pending"]
        ).values_list("course_id", flat=True)

       

        

        latest_registrations = registrations.filter(
            ~Q(course_id__in=courses_in_current_session),
            semester=current_semester_model,
            
        ).values("course_id").annotate(
            latest_registration_id=Subquery(
                registrations.filter(
                    ~Q(course_id__in=courses_in_current_session),
                    course_id=OuterRef("course_id"),
                    semester=current_semester_model,
                    
                ).order_by("-registration_date", "-id").values("id")[:1]
            )
        ).values("course_id", "latest_registration_id")

        carryover_base_registrations = registrations.filter(
            ~Q(course_id__in=courses_in_current_session),
            semester=current_semester_model,
            
        )
        courses_with_prereqs_met = [
            reg.course for reg in carryover_base_registrations
            if reg.course.prerequisites.count() == 0 or has_prerequisites_passed(student, reg.course)
        ]

        # Step 4: Filter carryover registrations where latest result is not passed
        # carryover_registrations = registrations.filter(
        #     ~Q(course_id__in=courses_in_current_session),
        #     id__in=Subquery(latest_registrations.values("latest_registration_id")),
        #     semester=current_semester_model,
            
        # ).exclude(
        #     id__in=Subquery(
        #         Result.objects.filter(
        #             registration_id=OuterRef("id"),
        #             grade_remark="passed"
        #         ).values("registration_id")
        #     )
        # ).distinct()

        carryover_registrations = registrations.filter(
            ~Q(course_id__in=courses_in_current_session),
            id__in=Subquery(latest_registrations.values("latest_registration_id")),
            semester=current_semester_model,
            course__in=courses_with_prereqs_met
        ).exclude(
            id__in=Subquery(
                Result.objects.filter(
                    registration_id=OuterRef("id"),
                    grade_remark="passed"
                ).values("registration_id")
            )
        ).distinct()

       
        


        # Step 6: Compulsory pending carryovers (only if prerequisites are now passed)
        compulsory_carryovers = Registration.objects.filter(
            ~Q(course_id__in=courses_in_current_session),
            student=student,
            session__year__lt=current_session_model.year,
            semester=current_semester_model,
            course__status="C",
            course__in=[course for course in Course.objects.all() if has_prerequisites_passed(student, course)],
            
        )

        # Apply latest registration filter to compulsory carryovers
        base_compulsory_carryovers = Registration.objects.filter(
            student=student,
            session__year__lt=current_session_model.year,
            semester=current_semester_model,
            course__status="C",
        )

        # Filter courses by prerequisites
        courses_with_prereqs_met = [
            reg.course for reg in base_compulsory_carryovers
            if reg.course.prerequisites.count() == 0 or has_prerequisites_passed(student, reg.course)
        ]

        # Debug: Print courses with prerequisites met
        print("Courses with Prerequisites Met:", [course.title for course in courses_with_prereqs_met])


        


    
        compulsory_carryovers = Registration.objects.filter(
            ~Q(course_id__in=courses_in_current_session),
            id__in=Subquery(
                base_compulsory_carryovers.filter(
                    course_id=OuterRef("course_id")
                ).order_by("-registration_date", "-id").values("id")[:1]
            ),
            student=student,
            session__year__lt=current_session_model.year,
            semester=current_semester_model,
            course__status="C",
            instructor_remark="pending",
            course__in=courses_with_prereqs_met
        ).distinct()


        # Debug: Print final carryovers
        print("Compulsory Carryovers:", list(compulsory_carryovers))

        print("carryover registration", carryover_registrations)

        print("compulsory_carryovers", compulsory_carryovers)

        carryover_courses_unique = (carryover_registrations | compulsory_carryovers).distinct()

        # Combine carryover_registrations and compulsory_carryovers
        combined_carryovers = (carryover_registrations | compulsory_carryovers)

        # Debug: Print combined carryovers
        print("Combined Carryovers:", list(combined_carryovers.values("course__title", "course__courseCode", "session__year", "id")))

        # Get the latest registration per course based on session__year
        latest_registrations = combined_carryovers.values("course_id").annotate(
            max_session_year=Max("session__year")
        ).values("course_id", "max_session_year")

        # Debug: Print latest registrations per course
        print("Latest Registrations:", list(latest_registrations))

        # Filter to keep only the latest registration per course
        carryover_courses_unique = combined_carryovers.filter(
            course_id__in=Subquery(
                latest_registrations.values("course_id")
            ),
            session__year__in=Subquery(
                latest_registrations.values("max_session_year")
            )
        ).distinct()

        # Debug: Print final unique carryovers
        # print("Carryover Courses Unique:", list(carryover_courses_unique.values("course__title", "course__courseCode", "session__year", "id")))

        # # Step 4: Annotate to get the latest registration date for each course
        # annotated_courses = registrations.annotate(
        #     latest_registration_date=Max("registration_date")
        # )

        # Step 4: Annotate to get the latest registration date for each course
        # annotated_courses = registrations.annotate(
        #     latest_registration_date=Max("registration_date")
        # )

        # annotated_courses= annotated_courses.filter(
        #     registration_date=F("latest_registration_date")
        # )

        # Step 5: Filter only the latest registrations
        # carryover_courses_unique = annotated_courses.filter(
        #     registration_date=F("latest_registration_date")
        # )

        

        # carryover_courses_unique = (carryover_registrations | prereq_carryovers).distinct()
        # carryover_courses_unique = (carryover_registrations).distinct()

        

    

        registrations = Registration.objects.filter(student=student).select_related(
            "session"
        )

        enrollment = (
            Enrollment.objects.filter(student=student).order_by("enrolled_date").first()
        )

        enrollment_year = int(enrollment.session.year.split("/")[0])


    
        # Calculate level for each session
        sessions_and_levels = []
        for registration in registrations:
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
                }
            )

        # cObjects = Course.objects.filter(department=student.department)
        # course_levels = sorted(set(x.level.name for x in cObjects))
        # confirmReg = confirmRegister.objects.filter(student=student)
        # unique_sessions = sorted(set(entry["session"] for entry in sessions_and_levels))
        # unique_levels = sorted(set(entry["level"] for entry in sessions_and_levels))
        # duration = len(unique_levels) if len(unique_levels) == len(unique_sessions) else 0

        cObjects = Course.objects.all().filter(department=student.department)
        course_levels = []
        for x in cObjects:
            course_levels.append(x.level.name)
        course_levels.sort(key=str)
        course_levels = list(set(course_levels))
        # print('course_levels', course_levels)

        confirmReg = confirmRegister.objects.filter(student=student)

        unique_sessions = sorted({entry["session"] for entry in sessions_and_levels})

        unique_levels = sorted({entry["level"] for entry in sessions_and_levels})


        duration = 0
        if len(unique_levels) == len(unique_sessions):
            duration = len(unique_levels)

        return render(
            request,
            "user/courses.html",
            {
                "courses": available_courses,
                "unavailable_courses": unavailable_courses,
                "student": student,
                "sess": current_session_model,
                "semes": current_semester_model,
                "carryover": carryover_courses_unique,
                "sessions_and_levels": sessions_and_levels,
                "unique_sessions": unique_sessions,
                "unique_levels": unique_levels,
                "duration": duration,
                "confirmReg": confirmReg,
                "stream": user.stream,
                "failed_results": failed_results,
                "failed_registration_ids": failed_registration_ids
            },
            
        )

    # return render(request, "user/courses.html", {"student": 'student'})

@login_required
@user_passes_test(is_student, login_url="/404")
def printCopy(request):
    if request.user.is_authenticated:
        user = request.user

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")  # Fallback if stream is invalid
            
        student = get_object_or_404(Student, user=user)
 

    if request.method == "GET":
        return redirect("/")

    try:
        if request.method == "POST":
            sess = request.POST["sess"]
            semes = request.POST["semes"]
            reg_courses = Registration.objects.filter(
                student=student,
                semester=get_object_or_404(Semester, name=semes),
                session=get_object_or_404(Session, year=sess),
                instructor_remark="approved"
            )

            confirmReg = confirmRegister.objects.filter(
                student=student,
                semester=get_object_or_404(Semester, name=semes),
                session=get_object_or_404(Session, year=sess),
            ).first()

            gen = generate_course_pdf(reg_courses, student, sess, semes, confirmReg)

            gen.output("fpdfdemo.pdf", "F")

            response = HttpResponse(
                gen.output(dest="S").encode("latin1"), content_type="application/pdf"
            )
            # response['Content-Disposition'] = 'attachment; filename="fpdfdemo.pdf"'

            response["Content-Disposition"] = 'inline; filename="preview.pdf"'
            return response
    except:
        messages.error(request, 'Something went wrong!')
        return redirect('stream_a:courses')

@login_required
@user_passes_test(is_student, login_url="/404")
def CourseDelete(request, id):
    if request.user.is_authenticated:
        user = request.user

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")  # Fallback if stream is invalid
        
        student = get_object_or_404(Student, user=user)

        level = get_object_or_404(Level, name=student.currentLevel)
        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()

        try:
            reg = Registration.objects.filter(id=id).first()
            if (
                reg.session == current_session_model
                and reg.semester == current_semester_model
                and reg.instructor_remark == "rejected"
            ):
                messages.info(request, f"Deleted {reg.course.title}!!")

                reg.delete()

                registrations = Registration.objects.filter(
                    student=student,
                    session=current_session_model,
                    semester=current_semester_model,
                )

                # Aggregate the total units by summing the 'unit' field of related courses
                total_units = registrations.aggregate(total_units=Sum("course__unit"))[
                    "total_units"
                ]

                # Handle the case where no registrations exist
                total_units = total_units or 0  # Default to 0 if no units are found

                print(f"Total units registered: {total_units}")

                confirm_reg, created = confirmRegister.objects.get_or_create(
                    student=student,
                    session=current_session_model,
                    semester=current_semester_model,
                    level=get_object_or_404(Level, name=student.currentLevel),
                )

                if not created:
                    # Update the total units and registration date if the instance already exists
                    confirm_reg.totalUnits = total_units
                    confirm_reg.registration_date = now().date()
                    confirm_reg.save()
                else:
                    # If a new instance was created, set the totalUnits and save
                    confirm_reg.totalUnits = total_units
                    confirm_reg.save()

                return redirect("stream_a:courses")
            else:
                messages.info(request, f"Request not allowed")
                return redirect("stream_a:courses")

        except:
            messages.info(request, f"Registered Course not available")
            return redirect("stream_a:courses")



@login_required
@user_passes_test(is_student, login_url="/404")
def ResultFilter(request):
    if request.user.is_authenticated:
        user = request.user

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")  # Fallback if stream is invalid
            
        student = get_object_or_404(Student, user=user)

        level = get_object_or_404(Level, name=student.currentLevel)
        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()

        # Get the earliest session the student was enrolled in
        earliest_session = student.entrySession.order_by("id").first()

        
        # Get all sessions from the earliest session onward
        if earliest_session:
            sessions_from_earliest = Session.objects.filter(id__gte=earliest_session.id)
            
        else:
            sessions_from_earliest = Session.objects.none()  # No sessions available

        # Print sessions for debugging

        if request.method == "POST":
            print(request.POST)
            sess = request.POST["session-select"]
            semes = request.POST["semester-select"]

            session = get_object_or_404(Session, year=sess)
            semester = get_object_or_404(Semester, name=semes)

            registration = Result.objects.filter(
                registration__student=student,
                registration__session=session,
                registration__semester=semester,
            )

            if registration.exists():
                # Get all attempts sorted by attempt date (latest first)
                attempts = registration.order_by("result_date")
                latest_attempt = attempts.first()

                # latest_attempt = Result.objects.filter(
                #     registration__student=student, registration__session=session, registration__semester=semester
                # ).values('registration_id').annotate(
                #     highest_attempt=Max('attempt_number')
                # )

                latest_attempt = (
                    Result.objects.filter(registration_id=OuterRef("registration_id"))
                    .values("registration_id")
                    .annotate(highest_attempt=Max("attempt_number"))
                    .values("highest_attempt")
                )

                latest_results = Result.objects.filter(
                    attempt_number=Subquery(latest_attempt),
                    registration__student=student,  # Ensure it is for the specific student
                )

                # Use list comprehension to keep the latest result for each course

                # for registration in attempts:
                #     if registration.registration.course.id not in processed_courses:
                #         processed_courses.append(registration)

                # latest_results = (
                #     registration.values('registration__course_id')  # Group by course
                #     .annotate(latest_attempt_date=Max('result_date'))  # Find the latest result_date
                # )

                # # Filter the results to include only the latest attempts
                # latest_attempts = Result.objects.filter(
                #     registration__course_id__in=[result['registration__course_id'] for result in latest_results],
                #     result_date__in=[result['latest_attempt_date'] for result in latest_results]
                # ).order_by('registration__course__courseCode')  # Optional ordering

                # Calculate total credit units
                total_credit_units = sum(
                    course.registration.course.unit for course in attempts
                )

                # Calculate total points
                total_points = sum(course.total_point for course in attempts)

                # Calculate GPA
                gpa = total_points / total_credit_units if total_credit_units > 0 else 0

                return render(
                    request,
                    "user/resultview.html",
                    {
                        "status": "success",
                        "latest_attempt": latest_attempt,
                        "all_attempts": attempts,
                        "results": latest_results,
                        "total_credit_units": total_credit_units,
                        "total_points": total_points,
                        "gpa": round(gpa, 2),
                        "total_course": len(attempts),
                        "session": session.year,
                        "semester": semester.name,
                        "stream": user.stream,
                    },
                )
            else:
                if not Result.objects.filter(
                    registration__session=session, registration__semester=semester
                ).exists():
                    messages.error(
                        request,
                        "Results have not been uploaded yet for this session and semester.",
                    )
                    return redirect("stream_a:result_filter")
                else:
                    messages.error(
                        request,
                        "No results found for this student in the selected session and semester.",
                    )
                    return redirect("stream_a:result_filter")

        return render(
            request, "user/results-new.html", {"student": student, "sessions": sessions_from_earliest, "stream": user.stream}
        )
    
@login_required
@user_passes_test(is_student, login_url="/404")
def ResultView(request):
    if request.user.is_authenticated:
        user = request.user

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")  # Fallback if stream is invalid
            
        student = get_object_or_404(Student, user=user)

        level = get_object_or_404(Level, name=student.currentLevel)
        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()

        if request.method == "POST":
            sess = request.POST["sess"]
            semes = request.POST["semes"]
            session = get_object_or_404(Session, year=sess)
            semester = get_object_or_404(Semester, name=semes)

            registration = Result.objects.filter(
                registration__student=student,
                registration__session=session,
                registration__semester=semester,
            )

            if registration.exists():
                # Get all attempts sorted by attempt date (latest first)
                print("reg i", registration)
                attempts = registration.order_by("result_date")
                print("reg ii", attempts)
                latest_attempt = attempts.first()

                # Calculate total credit units
                total_credit_units = sum(
                    course.registration.course.unit for course in attempts
                )

                # Calculate total points
                total_points = sum(course.total_point for course in attempts)

                # Calculate GPA
                gpa = total_points / total_credit_units if total_credit_units > 0 else 0

                reg_courses = Registration.objects.filter(
                    student=student,
                    semester=get_object_or_404(Semester, name=semes),
                    session=get_object_or_404(Session, year=sess),
                )

                confirmReg = confirmRegister.objects.filter(
                    student=student,
                    semester=get_object_or_404(Semester, name=semes),
                    session=get_object_or_404(Session, year=sess),
                ).first()

                gen = generate_pdf(attempts, student, sess, semes, confirmReg, gpa)

                gen.output("fpdfdemo.pdf", "F")

                response = HttpResponse(
                    gen.output(dest="S").encode("latin1"),
                    content_type="application/pdf",
                )
                # response['Content-Disposition'] = 'attachment; filename="fpdfdemo.pdf"'

                response["Content-Disposition"] = 'inline; filename="preview.pdf"'
                return response

        return render(request, "user/resultfilter.html", {"stream":user.stream})
    
@login_required
@user_passes_test(is_student, login_url="/404")
def Profile(request):
    if request.user.is_authenticated:
        user = request.user

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")  # Fallback if stream is invalid
            
        student = get_object_or_404(Student, user=user)
        level = get_object_or_404(Level, name=student.currentLevel)
        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()

        if request.method == "POST" and request.FILES.get("passport"):
            profilepic = request.FILES["passport"]

            # Rename file to avoid spaces and special characters
            filename = f"student_{student.user.id}.jpg"
            filepath = f"images/{filename}"

            # Save file properly
            student.passport.save(filepath, profilepic)

            student.save()
            return redirect('stream_a:profile')

        return render(request, "user/profile.html", {"student": student, "stream":user.stream})

@login_required
@user_passes_test(is_advisor, login_url="/404")
def AdvisorDashboard(request):
    if request.user.is_authenticated:
        user = request.user
        advisor = get_object_or_404(LevelAdvisor, user=user)

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:advisor_dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")
        

        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()

        total_students = len(Student.objects.filter(currentLevel=advisor.level, user__stream=advisor.user.stream))
        pending_reg = Registration.objects.filter(
            student__department=advisor.department,
            student__currentLevel=advisor.level,
            session=current_session_model,
            semester=current_semester_model,
            instructor_remark="pending",
        )
        rejected_reg = Registration.objects.filter(
            student__department=advisor.department,
            student__currentLevel=advisor.level,
            session=current_session_model,
            semester=current_semester_model,
            instructor_remark="rejected",
        )

       

        pending_students = Student.objects.filter(
            registration__course__department=advisor.department,
            registration__student__currentLevel=advisor.level,
            user__stream=advisor.user.stream,
            registration__session=current_session_model,
            registration__semester=current_semester_model,
            registration__instructor_remark="pending",
        ).distinct()

        return render(
            request,
            "levelAdvisor/dashboard.html",
            {
                "totalStudents": total_students,
                "totalPendingReg": len(pending_reg),
                "level": advisor.level,
                "pendingReg": pending_students,
                "totalRejectedReg": len(rejected_reg),
                "stream":user.stream,
            },
        )

def get_student_data(students, session, semester):
    """Helper function to build student data with approved and pending course counts."""
    student_data = []
    for student in students:
        registrations = Registration.objects.filter(
            student=student,
            session=session,
            semester=semester,
        )
        approved_count = registrations.filter(instructor_remark="approved").count()
        pending_count = registrations.filter(instructor_remark="pending").count()

        
        student_data.append({
            "student": student,
            "approved_courses": approved_count,
            "pending_courses": pending_count,
        })
    return student_data

@login_required
@user_passes_test(is_advisor, login_url="/404")
def StudentList(request):
    user = request.user
    advisor = get_object_or_404(LevelAdvisor, user=user)

    if user.stream != "a":
        if user.stream == "b":
            messages.info(request, "You have been redirected to your Stream B dashboard.")
            return redirect("stream_b:advisor_dashboard")
        messages.error(request, "Invalid stream for this user.")
        return redirect("/login/")

    current_session_model = Session.objects.filter(is_current=True).first()
    current_semester_model = Semester.objects.filter(is_current=True).first()

    context = {
        "curr_sess": current_session_model,
        "curr_semes": current_semester_model,
        "stream": user.stream,
    }

    if request.method == "POST":
        matricNo = request.POST.get("matricNo", "").strip()
        if matricNo:
            try:
                student = (
                    Student.objects.filter(
                        Q(matricNumber=matricNo) | Q(jambNumber=matricNo),
                        department=advisor.department,
                        currentLevel=advisor.level,
                        currentSession=current_session_model,
                    ).first()
                )
                if student:
                    student_data = get_student_data([student], current_session_model, current_semester_model)
                    context["student_data"] = student_data
                    return render(request, "levelAdvisor/student.html", context)
                else:
                    messages.error(request, f"Student not found!")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(request, "Matric number cannot be empty!")
        return redirect("stream_a:advisor_students")

    students = Student.objects.filter(
        department=advisor.department,
        currentLevel=advisor.level,
        currentSession=current_session_model,
        user__stream=advisor.user.stream,
    )
    context["student_data"] = get_student_data(students, current_session_model, current_semester_model)
    return render(request, "levelAdvisor/student.html", context)

@login_required
@user_passes_test(is_advisor, login_url="/404")
def AdvisorReg(request):
    if request.user.is_authenticated:
        user = request.user
        advisor = get_object_or_404(LevelAdvisor, user=user)

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:advisor_dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")

        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()
        courses = Course.objects.all()


       
        
        matricNo = request.GET.get("q")

        

        if matricNo != "":
            try:
                student = (
                    Student.objects.all()
                    .filter(
                        Q(matricNumber=matricNo) | Q(jambNumber=matricNo),
                        department=advisor.department,
                        currentLevel=advisor.level,
                        user__stream=user.stream,
                    )
                    .first()
                )
                
                if student:

                    enrollment = (
                        Enrollment.objects.filter(student=student)
                        .order_by("enrolled_date")
                        .first()
                    )

                    if not enrollment:
                        # Handle case where the student has no enrollment record
                        messages.info(request, f"No enrollment found!")
                        redirect(f"stream_a:advisor_reg")

                    enrollment_year = int(enrollment.session.year.split("/")[0])

                    registrations = Registration.objects.filter(
                        student__department=advisor.department,
                        student=student,
                        semester=current_semester_model,
                        session=current_session_model,
                    )

                    return render(
                        request,
                        "levelAdvisor/studentManagement.html",
                        {
                            "department": advisor.department,
                            "curr_sess": current_session_model,
                            "curr_semes": current_semester_model,
                            "student": student,
                            "matricNo": matricNo,
                            "courses": courses,
                            "registrations": registrations,
                            "stream": user.stream,
                        },
                    )
            except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")
                    return redirect("stream_a:advisor_reg")

        messages.info(request, f"Field cannot be empty!")
        redirect(f"stream_a:advisor_reg")
    return render(
        request,
        "levelAdvisor/studentManagement.html",
        {
            "department": advisor.department,
            "curr_sess": current_session_model,
            "curr_semes": current_semester_model,
            "stream": user.stream,
        },
    )



@login_required
@user_passes_test(is_advisor, login_url="/404")
def AdvisorDeleteStudentRegisteredCourse(request, id, matricNo):
    if request.user.is_authenticated:
        user = request.user
        advisor = get_object_or_404(LevelAdvisor, user=user)
        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:advisor_dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")

        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()
    try:
        student = get_object_or_404(Student, matricNumber=matricNo, department=advisor.department)
                
        regObjects = get_object_or_404(Registration, id=id, student=student)
        
        if (
            regObjects.session == current_session_model
            and regObjects.semester == current_semester_model
            and regObjects.instructor_remark != "approved"
        ):
            if Registration.objects.all().filter(id=id).exists():
                messages.info(
                    request, f"{regObjects.course.title} deleted successfully"
                )
                regObjects = Registration.objects.filter(id=id).delete()

                return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")
            messages.info(request, f"Registered Course not available")
            return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")
        messages.info(request, f"Cannot perform Opereation")
        return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")
    except:
        messages.info(request, f"Registered Course not available")
        return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")


@login_required
@user_passes_test(is_advisor, login_url="/404")
def AdvisorAddCourseStudentRegisteredCourse(request, matricNo):
    user = request.user
    advisor = get_object_or_404(LevelAdvisor, user=user)

    if user.stream != "a":
        if user.stream == "b":
            messages.info(request, "You have been redirected to your Stream B dashboard.")
            return redirect("stream_b:advisor_dashboard")
        messages.error(request, "Invalid stream for this user.")
        return redirect("/login/")

    # Validate query parameters
    courseId = request.GET.get("course")
    curr_session = request.GET.get("curr_session")
    curr_semester = request.GET.get("curr_semester")

    if not all([courseId, curr_session, curr_semester]):
        messages.error(request, "Missing required parameters: course, session, or semester.")
        return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")

    # Get current session and semester
    current_session_model = Session.objects.filter(is_current=True).first()
    current_semester_model = Semester.objects.filter(is_current=True).first()

    if not current_session_model or not current_semester_model:
        messages.error(request, "Current session or semester not set.")
        return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")

    # Find student
    student = (
        Student.objects.filter(
            Q(matricNumber=matricNo) | Q(jambNumber=matricNo),
            department=advisor.department,
            user__stream=user.stream,
        ).first()
    )

    if not student:
        messages.info(request, f"Student does not exist")
        return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")

    # Check session and semester
    if (
        curr_session != current_session_model.year
        or curr_semester != current_semester_model.name
    ):
        
        messages.info(request, f"Session or semester does not match current values.")
        return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")

    # Get course
    course = get_object_or_404(Course, id=courseId)

    # Validate course semester
    if course.semester.name != current_semester_model.name:
        messages.info(request, f"Invalid course for the current semester.")
        return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")

    # Check if already registered
    if Registration.objects.filter(
        student=student,
        course=course,
        session=current_session_model,
        semester=current_semester_model,
    ).exists():
        messages.info(request, f"Course already registered.")
        return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")

    # Create registration
    Registration.objects.create(
        student=student,
        course=course,
        session=current_session_model,
        semester=current_semester_model,
    )
    messages.success(request, f"Course {course.title} added successfully.")
    return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")

@login_required
@user_passes_test(is_advisor, login_url="/404")
def AdvisorApproveRejectReg(request, stats, id, matricNo):
    if request.user.is_authenticated:
        user = request.user
        advisor = get_object_or_404(LevelAdvisor, user=user)
        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream B dashboard.")
                return redirect("stream_b:advisor_dashboard")
            else:
                messages.error(request, "Invalid stream for this user.")
                return redirect("/login/")
        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()

        try:
            if stats == "approved" or stats == "rejected":
                reg = Registration.objects.filter(id=id).first()
                if (
                    reg.session == current_session_model
                    and reg.semester == current_semester_model
                ):
                    reg.instructor_remark = stats
                    reg.save()
                    messages.info(request, f"Registered Course {stats}!!")
                    return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")
                else:
                    messages.info(request, f"Request not allowed")
                    return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")
            else:
                messages.info(request, f"Invalid request")
                return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")
        except:
            messages.info(request, f"Registered Course not available")
            return redirect(f"{reverse('stream_a:advisor_reg')}?q={matricNo}")
    return render(request, "advisor/studentManagement.html")


def get_latest_failed_or_pending_courses(student):
    # Step 1: Get the current semester and session
    try:
        current_semester = Semester.objects.get(is_current=True)
        current_session = Session.objects.get(is_current=True)
    except ObjectDoesNotExist as e:
        raise ValueError("Ensure both the current semester and session are set.") from e

    # Step 2: Filter all registrations for the student
    registrations = Registration.objects.filter(student=student)

    # Step 3: Annotate courses with the latest registration date
    annotated_courses = registrations.annotate(
        latest_registration_date=Max("registration_date")
    )

    # Step 4: Filter for courses with the latest registration date
    latest_registrations = annotated_courses.filter(
        registration_date=F("latest_registration_date")
    )

    # Step 5: Filter pending or failed courses that are not in the current semester or session
    filtered_courses = latest_registrations.filter(
        Q(grade_remark__in=["pending", "failed"]),
        #     ~Q(semester=current_semester),
        #     ~Q(session=current_session)
    )

    return filtered_courses