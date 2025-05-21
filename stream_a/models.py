# stream_b/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from common.models import CustomUser, SessionBase, SemesterBase, CollegeBase, DepartmentBase, ProgrammeBase, LevelBase
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
import os

# Create your models here.
class Session(SessionBase):
    def __str__(self):
        return f"{self.year} (Stream A)"

class College(CollegeBase):
    def __str__(self):
        return f"{self.name} (Stream A)"

class Department(DepartmentBase):
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} (Stream A)"

class Programme(ProgrammeBase):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Level(LevelBase):
    def __str__(self):
        return self.name

class Semester(SemesterBase):
    def __str__(self):
        return f"{self.name} (Stream A)"
    
class Student(models.Model):
    STUDENTSTATUS_CHOICES = (
        ('inprogress', 'In Progress'),
        ('failed', 'Failed'),
        ('graduated', 'Graduated'),
    )
    GENDER_CHOICES = (
        ('f', 'Female'),
        ('m', 'Male'),
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='stream_a_student', primary_key=True)
    otherNames = models.CharField(blank=True, null=True, max_length=80)
    surname = models.CharField(blank=True, null=True, max_length=80)
    currentLevel = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='currentLevel', null=True, default=1)
    matricNumber = models.CharField(blank=True, null=True, max_length=30)
    jambNumber = models.CharField(blank=True, null=True, max_length=30)
    dateOfBirth = models.DateField()
    gender = models.CharField(blank=True, null=True, max_length=15, choices=GENDER_CHOICES)
    studentPhoneNumber = models.CharField(blank=True, null=True, max_length=15)
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='students', blank=True, null=True)
    entrySession = models.ManyToManyField(Session, through='Enrollment', related_name='entrySession')
    currentSession = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, related_name='current_students')
    # currentSemester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, related_name='current_students')
    # ... (keep other fields as is)
    primaryEmail = models.CharField(blank=True, null=True, max_length=120)
    studentEmail = models.CharField(blank=True, null=True, max_length=120)
    bloodGroup = models.CharField(blank=True, null=True, max_length=20)
    genoType = models.CharField(blank=True, null=True, max_length=20)
    modeOfEntry = models.CharField(blank=True, null=True, max_length=50)
    entryLevel =  models.ForeignKey(Level, on_delete=models.CASCADE,  null=True, default=1)
    degree = models.CharField(blank=True, null=True, max_length=50)
    nationality = models.CharField(blank=True, null=True, max_length=110)
    stateOfOrigin = models.CharField(blank=True, null=True, max_length=110)
    localGovtArea = models.CharField(blank=True, null=True, max_length=110)
    passport = models.ImageField('image', default='images/placeholder.png', null=True, blank=True)
    student_status = models.CharField(max_length=100, choices=STUDENTSTATUS_CHOICES, default='inprogress')

    def __str__(self):
        return f"{self.surname} - {self.matricNumber} (Stream A)"
    

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    enrolled_date = models.DateField()

    def __str__(self):
        return f"{self.student} in {self.session}"

class Course(models.Model):
    COURSE_CHOICES = (
        ('C', 'Compulsory'),
        ('E', 'Elective'),
        ('R', 'Required'),
    )
    CATEGORY_CHOICES = (
        ('nursing course', 'NC'),
        ('life science', 'LS'),
        ('non-nursing course', 'NNC'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(blank=True, null=True, max_length=500)
    courseCode = models.CharField(blank=True, null=True, max_length=15)
    unit = models.IntegerField(blank=True, null=True)
    status = models.CharField(blank=True, choices=COURSE_CHOICES, default='C', null=True, max_length=40)
    category = models.CharField(blank=True, choices=CATEGORY_CHOICES, default='NNC', null=True, max_length=40)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    programme = models.ManyToManyField(Programme, related_name='courses')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True)
    prerequisites = models.ManyToManyField("self", blank=True, symmetrical=False)

    def __str__(self):
        return f"{self.courseCode} (Stream A)"


class LevelAdvisor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='stream_a_advisor', primary_key=True)
    name = models.CharField(blank=True, null=True, max_length=500)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    passport = models.ImageField(upload_to="images/", default='images/placeholder.png', null=True, blank=True)
    stream = models.CharField(max_length=1, default='a')

    def __str__(self):
        return f'Level Advisor - {self.level.name} -{self.name}'
    


class Registration(models.Model):
    INSTRUCTOR_REMARK_CHOICES = (
        ('pending', 'pending'),
        ('approved', 'approved'),
        ('rejected', 'rejected')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE,  null=True, default=None)
    course = models.ForeignKey(Course, on_delete=models.CASCADE,  null=True, default=None)
    session = models.ForeignKey(Session, on_delete=models.CASCADE,  null=True, default=None)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE,  null=True, default=None)
    instructor_remark = models.CharField(max_length=50, choices=INSTRUCTOR_REMARK_CHOICES, null=True, default='pending')
    registration_date = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.id} - {self.student.surname} - {self.course} ({self.session}, {self.semester})"

class Result(models.Model):
    GRADE_REMARK_CHOICES = (
        ('passed', 'passed'),
        ('failed', 'failed'),
        ('pending', 'pending'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='results')
    attempt_number = models.PositiveIntegerField(default=1)  # Track the number of attempts (resits)
    grade = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    grade_type = models.CharField(max_length=5, null=True, blank=True)
    grade_point = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    total_point = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    grade_remark = models.CharField(max_length=20, choices=GRADE_REMARK_CHOICES, default='pending')
    passed = models.BooleanField(default=False)
    carried_over = models.BooleanField(default=False)
    result_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('registration', 'attempt_number')  # Prevent duplicate attempts for the same registration

    def __str__(self):
        return f"Result for {self.registration.student.surname} - {self.registration.course} (Attempt {self.attempt_number})"

    def save(self, *args, **kwargs):
        # Automatically update grade_type based on the grade
        if self.grade is not None:
            if self.registration.course.category == 'NC' or self.registration.course.category == 'LS':
                if self.grade >= 70:
                    self.grade_type = 'A'
                elif self.grade >= 60:
                    self.grade_type = 'B'
                elif self.grade >= 50:
                    self.grade_type = 'C'
                else:
                    self.grade_type = 'F'
            else:
                if self.grade >= 70:
                    self.grade_type = 'A'
                elif self.grade >= 60:
                    self.grade_type = 'B'
                elif self.grade >= 50:
                    self.grade_type = 'C'
                elif self.grade >= 45:
                    self.grade_type = 'D'
                else:
                    self.grade_type = 'F'

            # Update grade_remark based on whether the grade is a pass or fail
            if self.registration.course.category == 'NC' or self.registration.course.category == 'LS':
                self.grade_remark = 'passed' if self.grade >= 50 else 'failed'
            else:
                self.grade_remark = 'passed' if self.grade >= 45 else 'failed'

            if self.grade_type == 'A':
                self.grade_point = 4
            elif self.grade_type == 'B':
                self.grade_point = 3
            elif self.grade_type == 'C':
                self.grade_point = 2
            elif self.grade_type == 'D':
                self.grade_point = 1
            else:
                self.grade_point = 0

        if self.grade_type is not None and self.grade_point is not None:
            self.total_point = self.grade_point * self.registration.course.unit

        super().save(*args, **kwargs)

        
class confirmRegister(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE,  null=True, default=None)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, default=None)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE,  null=True, default=None)
    registration_date = models.DateField(auto_now_add=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    totalUnits = models.CharField(max_length=100, blank=True, null=True)
    gpa = models.CharField(max_length=100, blank=True, null=True)

@receiver(post_save, sender=Student)
def create_enrollment_for_student(sender, instance, created, **kwargs):
    if created:
        try:
            current_session = Session.objects.get(is_current=True)
            Enrollment.objects.create(student=instance, session=current_session, enrolled_date=now())
        except Session.DoesNotExist:
            print("No current session found for Stream A.")