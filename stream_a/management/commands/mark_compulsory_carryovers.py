# python manage.py mark_compulsory_carryovers

from django.core.management.base import BaseCommand
from django.db.models import Q
from stream_a.models import Student, Course, Registration, Session, Semester, confirmRegister, Level, Department
from common.models import  CustomUser
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from django.utils.timezone import now

class Command(BaseCommand):
    help = 'Marks unregistered compulsory courses as carryovers at the end of the session'

    def handle(self, *args, **kwargs):
        # Get the current session and semesters
        current_session = Session.objects.filter(is_current=True).first()
        if not current_session:
            self.stdout.write(self.style.ERROR('No current session found.'))
            return

        semesters = Semester.objects.all()  # Check both semesters in the session
        students = Student.objects.filter(currentSession=current_session)

        for student in students:
            print("students", student)
            # Get compulsory courses for the student's level, programme, and semesters
            compulsory_courses = Course.objects.filter(
                level=student.currentLevel,
                programme=student.programme,
                semester__in=semesters,
                status="C"
            )

            print("compulsory courses", compulsory_courses)

            for course in compulsory_courses:
                # Check if the course was registered in the current session
                registered = Registration.objects.filter(
                    student=student,
                    course=course,
                    session=current_session,
                    semester=course.semester
                ).exists()

                if not registered:
                    # Create carryover registration
                    Registration.objects.get_or_create(
                        student=student,
                        course=course,
                        session=current_session,
                        semester=course.semester,
                        defaults={"instructor_remark": "pending"}
                    )

                    confirm_reg, created = confirmRegister.objects.get_or_create(
                        student=student,
                        session=current_session,
                        semester=course.semester,
                        level=get_object_or_404(Level, name=student.currentLevel),
                    )

                    if not created:
                        # Update the total units and registration date if the instance already exists
                        confirm_reg.totalUnits = course.unit
                        confirm_reg.registration_date = now().date()
                        confirm_reg.save()
                    else:
                        # If a new instance was created, set the totalUnits and save
                        confirm_reg.totalUnits = course.unit
                        confirm_reg.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Marked {course.title} as carryover for {student.matricNumber}"
                        )
                    )

        self.stdout.write(self.style.SUCCESS('Completed marking compulsory carryovers.'))