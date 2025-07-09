# python manage.py import_students aconsaStudent_STREAM_A_data_template.csv
import csv
import os
import uuid
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.files import File
# from common.models import CustomUser, Student, Level, College, Department, Programme, Session, Enrollment

from common.models import *
from stream_a.models import *

class Command(BaseCommand):
    help = 'Import students from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f"File {csv_file_path} does not exist"))
            return

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                required_columns = {
                    'surname', 'otherNames', 'matricNumber', 
                    'dateOfBirth', 'gender', 'currentLevel', 'department', 
                    'programme', 'currentSession', 'entrySession'
                }
                if not all(col in reader.fieldnames for col in required_columns):
                    missing = required_columns - set(reader.fieldnames)
                    self.stdout.write(self.style.ERROR(f"Missing required columns: {missing}"))
                    return

                success_count = 0
                error_count = 0

                for row in reader:
                    try:
                        # Create CustomUser first
                        # Check if username already exists, if so, make it unique

                        print('primaryEmail', row["primaryEmail"])
                     
                        user, created = CustomUser.objects.get_or_create(
                            email=row["primaryEmail"],
                            defaults={
                                "username": row["primaryEmail"].strip(),
                                "first_name": row["otherNames"].strip(),
                                "last_name": row["surname"].strip(),
                                "user_type": "student",
                                "stream": 'b'
                            },
                        )

                        # user = CustomUser(
                        #     id=uuid.uuid4(),
                        #     username=row['primaryEmail'],
                        #     user_type='student'
                        # )
                        # Set a default password (e.g., matric number)
                        user.set_password(row['matricNumber'].strip())
                        user.save()

                        # Get related objects
                        current_level = Level.objects.get(name='nd1')  # or name=
                        department = Department.objects.get(name='nursing')  # or name=
                        programme = Programme.objects.get(name='general nursing')  # or name=

                        # Parse date of birth (assuming format: YYYY-MM-DD)
                        # dob = datetime.strptime(row['dateOfBirth'], '%Y-%m-%d').date()
                        dob = datetime.strptime(
                                    row["dateOfBirth"], "%d/%m/%Y"
                                ).strftime("%Y-%m-%d")
                        
                        # Create Student
                        student = Student(
                            user=user,
                            surname=row['surname'],
                            otherNames=row['otherNames'],
                            currentLevel=current_level,
                            matricNumber=row['matricNumber'],
                            jambNumber=row.get('jambNumber', None),
                            dateOfBirth=dob,
                            gender=row['gender'],
                            studentPhoneNumber=row.get('studentPhoneNumber', None),
                            department=department,
                            programme=programme,
                            currentSession=Session.objects.get(year='2023/2024'),
                            primaryEmail=row.get('primaryEmail', None),
                            studentEmail=row.get('studentEmail', None),
                            bloodGroup=row.get('bloodGroup', None),
                            genoType=row.get('genoType', None),
                            modeOfEntry=row.get('modeOfEntry', None),
                            entryLevel=current_level,
                            degree='hnd',
                            nationality='nigerian',
                            stateOfOrigin=row.get('stateOfOrigin', None),
                            localGovtArea=row.get('localGovtArea', None),
                        )

                        student.save()

                        student.entrySession.set([Session.objects.get(year='2023/2024')])

                        # Handle college if provided
                        if 'college' in row and row['college']:
                            student.college = College.objects.get(name='achievers college of nursing sciences, akure')

                       

                        student.save()

                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Successfully imported student: {student.matricNumber}"
                        ))

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"Error importing student {row.get('matricNumber', 'unknown')}: {str(e)}"
                        ))
                        error_count += 1

                self.stdout.write(self.style.SUCCESS(
                    f"Import completed: {success_count} students imported, {error_count} errors"
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading CSV file: {str(e)}"))
