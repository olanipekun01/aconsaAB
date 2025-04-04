from django import forms
from common.models import CustomUser
# Student, Instructor, Department
from django.contrib.auth.forms import UserCreationForm

from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm



class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = "__all__"


class UserSignupForm(forms.ModelForm):
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'user_type']


# class StudentSignupForm(forms.ModelForm):
#     class Meta:
#         model = Student
#         fields = ['otherNames', 'surname', 'entryLevel', 'matricNumber', 'dateOfBirth', 'gender', 'studentPhoneNumber']


# class InstructorSignupForm(forms.ModelForm):
#     class Meta:
#         model = Instructor
#         fields = ['name', 'phoneNumber']