from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.
from django.contrib import messages
from common.models import CustomUser  
from .models import Student, Level, Session, Semester  

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

