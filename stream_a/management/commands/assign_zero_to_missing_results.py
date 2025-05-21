from django.core.management.base import BaseCommand
from django.db.models import Q, OuterRef, Subquery
from stream_a.models import Registration, Result, Session, Semester, Student
from django.utils.timezone import now

class Command(BaseCommand):
    help = 'Assigns a score of 0 to approved registrations with no results for a given session and semester.'

    def add_arguments(self, parser):
        parser.add_argument('--session', type=str, required=True, help='Session year (e.g., "2023/2024")')
        parser.add_argument('--semester', type=str, required=True, help='Semester name (e.g., "First")')
        parser.add_argument('--student_id', type=str, help='Matric number of a specific student (e.g., "TEST123")')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    def handle(self, *args, **options):
        session_year = options['session']
        semester_name = options['semester']
        student_id = options['student_id']
        dry_run = options['dry_run']

        # Validate session and semester
        try:
            session = Session.objects.get(year=session_year)
        except Session.DoesNotExist:
            self.stderr.write(f"Error: Session '{session_year}' does not exist.")
            return

        try:
            semester = Semester.objects.get(name=semester_name)
        except Semester.DoesNotExist:
            self.stderr.write(f"Error: Semester '{semester_name}' does not exist.")
            return

        # Build queryset for approved registrations
        registrations = Registration.objects.filter(
            session=session,
            semester=semester,
            instructor_remark="approved"
        )

        # Filter by student if provided
        if student_id:
            try:
                student = Student.objects.get(matricNumber=student_id)
                registrations = registrations.filter(student=student)
            except Student.DoesNotExist:
                self.stderr.write(f"Error: Student with matric number '{student_id}' does not exist.")
                return

        # Find registrations with no results
        registrations_without_results = registrations.filter(
            ~Q(id__in=Subquery(
                Result.objects.filter(
                    registration__session=session,
                    registration__semester=semester
                ).values("registration_id")
            ))
        )

        # Log the registrations that will be affected
        count = registrations_without_results.count()
        self.stdout.write(f"Found {count} approved registrations without results for session {session_year}, semester {semester_name}.")
        if count == 0:
            self.stdout.write("No action needed.")
            return

        if dry_run:
            self.stdout.write("Dry run: The following registrations would be assigned a score of 0:")
        else:
            self.stdout.write("Assigning a score of 0 to the following registrations:")

        for reg in registrations_without_results:
            self.stdout.write(
                f"Student: {reg.student.matricNumber}, Course: {reg.course.title} ({reg.course.code}), "
                f"Session: {reg.session.year}, Semester: {reg.semester.name}"
            )

        if dry_run:
            self.stdout.write("Dry run complete. No changes were made.")
            return

        # Assign score of 0
        created_results = 0
        for reg in registrations_without_results:
            # Determine attempt_number
            existing_attempts = Result.objects.filter(
                registration__student=reg.student,
                registration__course=reg.course
            ).aggregate(max_attempt=Max("attempt_number"))
            attempt_number = (existing_attempts["max_attempt"] or 0) + 1

            # Create Result
            Result.objects.create(
                registrationc=reg,
                score=0,
                grade_remark="failed",
                attempt_number=attempt_number,
                date_added=now()
            )
            created_results += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {created_results} Result records with score 0 for session {session_year}, semester {semester_name}."
        ))