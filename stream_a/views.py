from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.
from django.contrib import messages
from common.models import CustomUser

from .models import *
from django.db.models import Q, F, OuterRef, Subquery, Max

import uuid
import random
import string
import json
from django.core.exceptions import ObjectDoesNotExist

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

    return render(request, "user/dashboard.html", {"student": student})

@login_required
@user_passes_test(is_student, login_url="/404")
def Courses(request):
    if request.user.is_authenticated:
        user = request.user

        if user.stream != "a":
            # Redirect to the correct stream's dashboard
            if user.stream == "b":
                messages.info(request, "You have been redirected to your Stream A dashboard.")
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

            # Aggregate the total units by summing the 'unit' field of related courses
            total_units = registrations.aggregate(total_units=Sum("course__unit"))[
                "total_units"
            ]

            # Handle the case where no registrations exist
            total_units = total_units or 0

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
            },
        )

    # return render(request, "user/courses.html", {"student": 'student'})
