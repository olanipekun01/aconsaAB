# python manage.py register_second_semester_courses

import uuid
from django.core.management.base import BaseCommand
from stream_a.models import Student, confirmRegister, Level,  Course, Session, Semester, Registration, Department, Programme

class Command(BaseCommand):
    help = 'Register all students for first-semester courses'

    def handle(self, *args, **options):
        try:
            # Get all students (assuming there are exactly 34)
            students = Student.objects.all()
            student_count = students.count()
            if student_count != 34:
                self.stdout.write(self.style.WARNING(
                    f"Expected 34 students, found {student_count}. Proceeding with all available students."
                ))

            # Get the current session
            try:
                current_session = Session.objects.get(is_current=True)
            except Session.DoesNotExist:
                self.stdout.write(self.style.ERROR("No current session found. Please mark a session as current."))
                return

            # Get the first semester (adjust this based on how you identify it)
            try:
                second_semester = Semester.objects.get(name='second')  # Or use id=1, or another identifier
            except Semester.DoesNotExist:
                self.stdout.write(self.style.ERROR("Second semester not found. Please create a 'First Semester' in Semester model."))
                return

            # Get all first-semester courses
            second_semester_courses = Course.objects.filter(semester=second_semester, programme=Programme.objects.get(name='general nursing'))
            if not second_semester_courses.exists():
                self.stdout.write(self.style.ERROR("No courses found for the first semester."))
                return

            success_count = 0
            error_count = 0

            # Register each student for each first-semester course
            for student in students:
                for course in second_semester_courses:
                    try:
                        # Check if registration already exists to avoid duplicates
                        if not Registration.objects.filter(
                            student=student,
                            course=course,
                            session=current_session,
                            semester=second_semester
                        ).exists():
                            registration = Registration(
                                id=uuid.uuid4(),
                                student=student,
                                course=course,
                                session=current_session,
                                semester=second_semester,
                                instructor_remark='approved'
                            )
                            registration.save()
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS(
                                f"Registered {student.matricNumber} for {course.courseCode}"
                            ))
                        else:
                            self.stdout.write(self.style.WARNING(
                                f"Skipping {student.matricNumber} for {course.courseCode} - already registered"
                            ))

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"Error registering {student.matricNumber} for {course.courseCode}: {str(e)}"
                        ))
                        error_count += 1
                
                confirm_reg = confirmRegister(
                    id=uuid.uuid4(),
                    student=student,
                    session=current_session,
                    semester=second_semester,
                    level=Level.objects.get(name=student.currentLevel),
                    totalUnits = '29'
                )

                confirm_reg.save()

            self.stdout.write(self.style.SUCCESS(
                f"Registration completed: {success_count} registrations created, {error_count} errors"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))