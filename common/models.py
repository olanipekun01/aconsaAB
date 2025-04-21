# common/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password
import uuid
from django.utils.timezone import now

STREAM_CHOICES = (
    ('a', 'Stream A'),
    ('b', 'Stream B'),
)

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('leveladvisor', 'LevelAdvisor'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES)
    stream = models.CharField(max_length=1, choices=STREAM_CHOICES)

    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password = make_password(raw_password)
        
    def check_password(self, raw_password):
        """Check the password against the stored hashed password."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.username} ({self.stream})"
    
class SessionBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    year = models.CharField(max_length=9)  # e.g., '2023/2024'
    is_current = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.is_current:
            self.__class__.objects.filter(is_current=True).exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)

    

class SemesterBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=True, null=True, max_length=80)
    is_current = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.is_current:
            self.__class__.objects.filter(is_current=True).exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)

# Add other base models as needed (e.g., CollegeBase, DepartmentBase, etc.)
class CollegeBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=True, null=True, max_length=500)

    class Meta:
        abstract = True

class DepartmentBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=True, null=True, max_length=500)

    class Meta:
        abstract = True

class ProgrammeBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, null=True, blank=True)
    duration = models.IntegerField(blank=True, null=True)
    degree = models.CharField(blank=True, null=True, max_length=50)

    class Meta:
        abstract = True

class LevelBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(blank=True, null=True, max_length=80)

    class Meta:
        abstract = True


class Instructor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='stream_a_instructor', primary_key=True)
    name = models.CharField(blank=True, null=True, max_length=500)
    phoneNumber = models.CharField(blank=True, null=True, max_length=15)
    departmental_email = models.CharField(blank=True, null=True, max_length=90)
    passport = models.ImageField(upload_to="images/", default='images/placeholder.png', null=True, blank=True)
    preferred_stream = models.CharField(
        max_length=1,
        choices=[("a", "Stream A"), ("b", "Stream B")],
        default="a",
        help_text="The stream the instructor prefers to view."
    )
    
    def __str__(self):
        return self.name


    