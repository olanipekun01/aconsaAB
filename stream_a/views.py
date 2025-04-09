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
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site

from .models import *

UserModel = get_user_model()


# Role check for students
def is_student(user):
    return user.is_authenticated and user.user_type == "student"


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
            # sess = request.POST["sess"]
            # semes = request.POST["semes"]
            totalUnit = request.POST["totalUnit"]
            # Filter registrations for the student, session, and semester
            registrations = Registration.objects.filter(
                student=student,
                session=current_session_model,
                semester=current_semester_model,
            )

            new_courses = Course.objects.filter(id__in=courses)
            new_units = new_courses.aggregate(total_units=Sum("unit"))["total_units"] or 0

            # Aggregate the total units by summing the 'unit' field of related courses
            total_units = registrations.aggregate(total_units=Sum("course__unit"))[
                "total_units"
            ]

            # Handle the case where no registrations exist
            total_units = total_units or 0

            total_units = total_units + new_units

            if total_units <= 5:
                for id in courses:

                    course = (get_object_or_404(Course, id=id),)
                    semester = current_semester_model

                    course_exist = Registration.objects.create(
                        student=student,
                        course=get_object_or_404(Course, id=id),
                        session=current_session_model,
                        semester=current_semester_model,
                    )
                    course_exist.save()

                # Default to 0 if no units are found

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
                messages.info(request, "Course added")
                return redirect("stream_a:courses")
            messages.error(request, "Exceeded maximum units")
            return redirect("stream_a:courses")

        level = get_object_or_404(Level, name=student.currentLevel)
        current_session_model = Session.objects.filter(is_current=True).first()
        current_semester_model = Semester.objects.filter(is_current=True).first()
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
                request, "No current semester is set. Please set one as current."
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
        ).values_list("course", flat=True)

        courses = courses.exclude(id__in=registered_courses)

        # Step 1: Retrieve the current session and semester
        current_session = Session.objects.filter(is_current=True).first()
        current_semester = Semester.objects.filter(is_current=True).first()

        if not current_session or not current_semester:
            messages.error(
                request, "No current semester is set. Please set one as current."
            )
            return redirect("stream_a:courses")

        # registrations = Registration.objects.filter(student=student)

        # # Step 2: Filter registrations not in the current session AND current semester
        # registrations = registrations.filter(
        #     ~Q(session=current_session) & Q(semester=current_semester)
        # )

        # # Debugging: Print the filtered registrations
        # print("Registrations not in current session and semester:", registrations)

        # annotated_courses = registrations.annotate(latest_registration_date=Max('registration_date'))
        # print('annotated_courses', annotated_courses)

        # # Step 3: Filter only the latest registrations
        # carryover_courses_unique = annotated_courses.filter(
        #     registration_date=F('latest_registration_date')
        # )

        latest_attempts = (
            Result.objects.filter(
                registration__student=student  # Filter by the specific student
            )
            .values("registration_id")
            .annotate(highest_attempt=Max("attempt_number"))
        )

        # print('latests', latest_attempts)

        # Step 2: Filter results with the highest attempt where the grade remark is not 'passed'
        # failed_results = Result.objects.filter(
        #     Q(attempt_number__in=[attempt['highest_attempt'] for attempt in latest_attempts]),
        #     registration__student=student,  # Ensure we only consider the same student
        #     grade_remark__in=['failed', 'pending']
        # )

        # failed_results = Result.objects.filter(
        #     Q(
        #         *[
        #             Q(registration_id=attempt['registration_id'], attempt_number=attempt['highest_attempt'])
        #             for attempt in latest_attempts
        #         ]
        #     ),
        #     grade_remark__in=['failed', 'pending']  # Filter for failed or pending results
        # )

        # print('results', failed_results)

        # Step 1: Verify latest attempts
        latest_attempts = (
            Result.objects.filter(registration__student=student)
            .values("registration_id")
            .annotate(highest_attempt=Max("attempt_number"))
        )
        # print("Latest Attempts:", list(latest_attempts))

        # Step 2: Construct the query for failed results
        conditions = [
            Q(
                registration_id=attempt["registration_id"],
                attempt_number=attempt["highest_attempt"],
            )
            for attempt in latest_attempts
        ]

        if conditions:
            failed_results = Result.objects.filter(
                reduce(lambda x, y: x | y, conditions),  # Combine conditions with OR
                grade_remark__in=["failed", "pending"],
            )
            # print("Failed Results:", list(failed_results))
        else:
            failed_results = Result.objects.none()  # No conditions mean no results

        # Final debug print
        # print("Final Failed Results:", failed_results)

        # Step 1: Filter all registrations for the student
        registrations = Registration.objects.filter(student=student)

        # Step 2: Identify courses registered in the current session
        courses_in_current_session = registrations.filter(
            session=current_session
        ).values_list("course_id", flat=True)

        # Step 3: Filter registrations not in the current session, but in the current semester,
        # and exclude any course that has been registered in the current session
        registrations = registrations.filter(
            ~Q(
                course_id__in=courses_in_current_session
            ),  # Exclude courses registered in current session
            semester=current_semester,  # Include only courses in current semester
        )

        registrations = registrations.filter(
            id__in=failed_results.values_list("registration_id", flat=True),
            student=student,  # Additional filter for the same student
        )

        # Debugging: Print the filtered registrations
        # print("Registrations not in current session but in current semester:", registrations)

        # Step 4: Annotate to get the latest registration date for each course
        annotated_courses = registrations.annotate(
            latest_registration_date=Max("registration_date")
        )
        # print('Annotated courses:', annotated_courses)

        # Step 5: Filter only the latest registrations
        carryover_courses_unique = annotated_courses.filter(
            registration_date=F("latest_registration_date")
        )

        # Debugging: Print final carryover courses
        # print("Final Carryover Courses:", carryover_courses_unique)

        # print('latest_registrations', carryover_courses_unique)

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

        # courses = Course.objects.all()

        duration = 0
        if len(unique_levels) == len(unique_sessions):
            duration = len(unique_levels)

        return render(
            request,
            "user/courses.html",
            {
                "courses": courses,
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