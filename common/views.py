from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser

def is_student(user):
    # print("User", User.role)
    return user.user_type == "student"
    # return True


def is_instructor(user):
    return user.user_type == "instructor"


def is_advisor(user):
    return user.user_type == "leveladvisor"



def loginView(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        
        try:
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                # Redirect based on user_type and stream
                if user.user_type == "student":
                    if user.stream == "a":
                        return redirect("stream_a:dashboard")
                    elif user.stream == "b":
                        return redirect("stream_b:dashboard")
                elif user.user_type == "instructor":
                    return redirect("/instructor/dashboard")  # Define this URL later
                elif user.user_type == "leveladvisor":
                    return redirect("/advisor/dashboard")  # Define this URL later
                else:
                    messages.error(request, "Unknown user type.")
                    return redirect("/login/")
            else:
                messages.error(request, "Invalid credentials!")
                return redirect("/login/")
    
        except User.DoesNotExist:
            messages.info(request, f"Invalid credentials!")
            return redirect("/login/")

    return render(request, "common/login.html")

def logoutView(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("/login")


@login_required
@user_passes_test(is_student, login_url="/404")
def changePassword(request):
    if request.method == "POST":
        old_password = request.POST["oldpassword"]
        new_password = request.POST["newpassword"]
        confirm_password = request.POST["newpassword"]

        if new_password != confirm_password:
            return render(
                request, "user/changepassword.html", {"error": "Use same password"}
            )

        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, "common/change_password.html")

        user = request.user

        if user.check_password(old_password):
            user.set_password(new_password)
            user = auth.authenticate(username=user.username, password=new_password)
            auth.login(request, user)
            messages.success(request, "Password changed successfully!")
            if user.user_type == "student":
                return redirect(f"stream_{user.stream}:change_password")
            elif user.user_type == "instructor":
                return redirect("instructor_change_password") 
            elif user.user_type == "leveladvisor":
                return redirect("level_advisor_change_password")
        else:
            messages.error(request, "Incorrect old password.")
            return render(request, "common/change_password.html")

    return render(request, "common/changepassword.html")

@login_required
def Redirect(request):
    if request.user.is_authenticated:
        user = request.user

        if user is not None:
            auth.login(request, user)
            # Redirect based on user_type and stream
            if user.user_type == "student":
                if user.stream == "a":
                    return redirect("stream_a:dashboard")
                elif user.stream == "b":
                    return redirect("stream_b:dashboard")
            elif user.user_type == "instructor":
                return redirect("/instructor/dashboard")  
            elif user.user_type == "leveladvisor":
                return redirect("/advisor/dashboard")  
            else:
                messages.error(request, "Unknown user type.")
                return redirect("/login/")
        else:
            messages.error(request, "Invalid credentials!")
            return redirect("/login/")
    return render(request, "common/login.html")