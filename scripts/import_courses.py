import csv
import os
import uuid
from django.core.management.base import BaseCommand
from app.models import Course, Department, Programme, Level, Semester

class Command(BaseCommand):
    help = 'Import courses from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        # Check if file exists
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f"File {csv_file_path} does not exist"))
            return

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Verify required columns
                required_columns = {'title', 'courseCode', 'unit', 'department', 'level', 'semester'}
                if not all(col in reader.fieldnames for col in required_columns):
                    missing = required_columns - set(reader.fieldnames)
                    self.stdout.write(self.style.ERROR(f"Missing required columns: {missing}"))
                    return

                success_count = 0
                error_count = 0

                for row in reader:
                    try:
                        # Get or create related objects
                        department = Department.objects.get(name=row['department'])  # or use name=row['department']
                        level = Level.objects.get(name=row['level'])  # or use name=row['level']
                        semester = Semester.objects.get(name=row['semester'])  # or use name=row['semester']

                        # Create course object
                        course = Course(
                            id=uuid.uuid4(),
                            title=row['title'],
                            courseCode=row['courseCode'],
                            unit=int(row['unit']) if row['unit'] else None,
                            status=row.get('status', 'C'),  # Default to 'C' if not provided
                            category=row.get('category', 'NNC'),  # Default to 'NNC' if not provided
                            department=department,
                            level=level,
                            semester=semester
                        )
                        course.save()

                        # Handle programmes (assuming comma-separated IDs or names)
                        if 'programme' in row and row['programme']:
                            programme_list = row['programme'].split(',')
                            for prog in programme_list:
                                try:
                                    programme = Programme.objects.get(name=prog.strip())  # or use name=prog.strip()
                                    course.programme.add(programme)
                                except Programme.DoesNotExist:
                                    self.stdout.write(self.style.WARNING(
                                        f"Programme {prog} not found for course {course.courseCode}"
                                    ))

                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Successfully imported course: {course.courseCode}"
                        ))

                    except Department.DoesNotExist:
                        self.stdout.write(self.style.ERROR(
                            f"Department {row['department']} not found for course {row['courseCode']}"
                        ))
                        error_count += 1
                    except Level.DoesNotExist:
                        self.stdout.write(self.style.ERROR(
                            f"Level {row['level']} not found for course {row['courseCode']}"
                        ))
                        error_count += 1
                    except Semester.DoesNotExist:
                        self.stdout.write(self.style.ERROR(
                            f"Semester {row['semester']} not found for course {row['courseCode']}"
                        ))
                        error_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"Error importing course {row['courseCode']}: {str(e)}"
                        ))
                        error_count += 1

                self.stdout.write(self.style.SUCCESS(
                    f"Import completed: {success_count} courses imported, {error_count} errors"
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading CSV file: {str(e)}"))
