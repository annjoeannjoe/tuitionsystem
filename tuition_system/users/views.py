from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from .models import User, Student, Admin, Announcement, Tuition_Classes, Enrolment, Calendar_Events, Subject_Evaluation
from django.contrib.auth.hashers import make_password,check_password
from datetime import datetime
from django.contrib.auth import update_session_auth_hash, logout as auth_logout, get_user_model
from django.views.decorators.cache import cache_control
from django.urls import reverse
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.utils import timezone
import os,re
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.paginator import Paginator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime, time
import pytz
from pytz import timezone
from django.utils import timezone
import plotly.express as px
import plotly.graph_objects as go
from django.db.models.functions import TruncMonth
from django.db.models import Count, Case, When, Value, CharField
from collections import defaultdict

def register (request):
    # Fetch all subjects from the database
    subjects = Tuition_Classes.objects.all()

    # Filter unique subjects for Kindergarten level
    kindergarten_subjects = set()
    for subject in subjects:
        if subject.tuition_class_study_level == "Kindergarten":
            kindergarten_subjects.add(subject.subject)

    primary_subjects = {
        'sk':{
            'std1': set(),
            'std2': set(),
            'std3': set(),
            'std4': set(),
            'std5': set(),
            'std6': set(),
        },
        'sjkc':{
            'std1': set(),
            'std2': set(),
            'std3': set(),
            'std4': set(),
            'std5': set(),
            'std6': set(),
        }
    }

    for subject in subjects:
        if subject.tuition_class_study_level.startswith("Primary"):
            components = subject.tuition_class_study_level.split()
            school_type = components[1]
            primary_level = components[2]

            if school_type == 'sk':
                primary_subjects['sk'][primary_level].add(subject.subject)
            elif school_type == 'sjkc':
                primary_subjects['sjkc'][primary_level].add(subject.subject)

    secondary_subjects = {
        'form1': set(),
        'form2': set(),
        'form3': set(),
        'form4': set(),
        'form5': set(),
    }

    for subject in subjects:
        if subject.tuition_class_study_level.startswith("Secondary"):
            components = subject.tuition_class_study_level.split()
            secondary_level=components[1]

            secondary_subjects[secondary_level].add(subject.subject)

    context = {
        'subjects': subjects,
        'kindergarten_subjects': kindergarten_subjects,
        'primary_subjects': primary_subjects,
        'secondary_subjects': secondary_subjects,

    }

    if request.method =='POST':
        email = request.POST['email']

        #check if a user with this email already exists
        try: 
            existing_user = User.objects.get(email=email)
            messages.error(request, 'An account with this email already exists. Please login.')
            return render(request, 'login.html', {'message': 'An account with this email already exists. Please login.','email':email})

        except User.DoesNotExist:
            pass

        # Create a new user object
        new_user = User()
        new_user.full_name = request.POST['fullname']
        new_user.email=email
        new_user.password = make_password(request.POST['password'])
        new_user.phone_no = request.POST['phoneNo'] 
        new_user.role = 'STUDENT' # set all the new user's role as student
        

        # Create a new student object with user as foreign key
        student = Student()
        student.user = new_user
        #student = Student.objects.get(user_id=id)

        student.school_level = request.POST['school_level']
        if student.school_level == 'primary':
            student.primary_school_type = request.POST['primary_school_type']
            if student.primary_school_type == 'sk':
                student.sk_level = request.POST['sk_level']
            elif student.primary_school_type == 'sjkc':
                student.sjkc_level = request.POST['sjkc_level']
        elif student.school_level == 'secondary':
            student.secondary_level = request.POST['secondary_level']

        student.startdate = datetime.strptime(request.POST['startdate'], '%Y-%m-%d').date()
        student.classin_phoneno = request.POST['classin_phoneno']
        phone2_country_code = request.POST['parent_phoneno2_code']

        phone2_number = request.POST['parent_phoneno2']
        parent_phoneno2 = f"{phone2_country_code}{phone2_number}"
        student.parent_phoneno2 = parent_phoneno2
    

        # Handle the bankin_receipt uploaded file
        bankin_receipt = request.FILES.get('bankin_receipt')
        if bankin_receipt:

            # Generate a new filename based on the user's username
            username = new_user.full_name
            extension = os.path.splitext(bankin_receipt.name)[-1]
            new_filename = f"{username}_BankInReceipt{extension}"

            #Assign the new filename to the uploaded file
            bankin_receipt.name = new_filename
            
            # Save the uploaded file (bankin_receipt)
            student.bankin_receipt = bankin_receipt

        student.student_phoneno = request.POST['student_phoneno']
        student.student_ic_number = request.POST['student_ic_number']

        # Handle the student_ic_photo uploaded file
        ic_photo = request.FILES.get('student_ic_photo')
        if ic_photo:
            
            # Geerate a new filename based on the user's username
            username = new_user.full_name
            extension = os.path.splitext(ic_photo.name)[-1]
            new_filename = f"{username}_IcPhoto{extension}"

            # Assign the new filename to the uploaded file
            ic_photo.name = new_filename

            # Save the uploaded file (ic_photo)
            student.student_ic_photo = ic_photo

        # Handle the student_photo uploaded file
        student_photo = request.FILES.get('student_photo')
        if student_photo:

            # Generate a new filename based on the user's username
            username = new_user.full_name
            extension = os.path.splitext(student_photo.name)[-1]
            new_filename = f"{username}_StudentPhoto{extension}"

            # Assign the new filename to the uploaded file
            student_photo.name = new_filename
            
            # Save the uploaded file (student_photo)
            student.student_photo = student_photo

        student.school_name = request.POST['school_name']
        new_user.street1 = request.POST['street1']
        new_user.street2 = request.POST['street2']
        new_user.city = request.POST['city']
        new_user.postalcode = request.POST['postalcode']
        new_user.state = request.POST['state']

        # know us from field
        selected_options=[]
        if 'facebook' in request.POST:
            selected_options.append('Facebook')
        if 'instagram' in request.POST:
            selected_options.append('Instagram')
        if 'google' in request.POST:
            selected_options.append('Google')
        if 'tiktok' in request.POST:
            selected_options.append('Tik Tok')
        if 'friend' in request.POST:
            selected_options.append('Friend')
        if 'xhs' in request.POST:
            selected_options.append('小红书')
        if 'sibling' in request.POST:
            selected_options.append('Sibling or Family Member')

        if 'other' in request.POST:
            other_know_us_from = request.POST.get('displayOther','')
            if other_know_us_from:
                selected_options.append(other_know_us_from)

        know_us_from =','.join(selected_options)
        student.know_us_from = know_us_from

        student.terms_and_conditions = True

        new_user.save()
        student.save()

        # Now that user and student attribute are set, create enrolment if applicable
        if student.school_level == 'kindergarten':
            for subject in kindergarten_subjects:
                selected_timeslot_id = request.POST.get(subject)
                if selected_timeslot_id and selected_timeslot_id != "0": # Check for not enrolling
                    selected_tuition_class = Tuition_Classes.objects.get(id=selected_timeslot_id)
                    if selected_tuition_class.tuition_class_study_level == "Kindergarten":
                        enrolment = Enrolment(
                            request_type = 'Add',
                            request_status = 'Pending',
                            enrolment_status = 'Active',
                            tuition_classes = selected_tuition_class,
                            student = student
                        )
                        enrolment.save()
        elif student.school_level == 'primary':
            student.primary_school_type = request.POST['primary_school_type']
            if student.primary_school_type == 'sk':
                student.sk_level = request.POST['sk_level']
                for primary_level, subjects in primary_subjects['sk'].items():
                    for subject in subjects:
                        selected_timeslot_id = request.POST.get(subject)
                        if selected_timeslot_id and selected_timeslot_id != "0":
                            selected_tuition_class = Tuition_Classes.objects.get(id = selected_timeslot_id)
                            if selected_tuition_class.tuition_class_study_level == f"Primary sk {primary_level}":
                                enrolment = Enrolment(
                                    request_type = 'Add',
                                    request_status = 'Pending',
                                    enrolment_status = 'Active',
                                    tuition_classes = selected_tuition_class,
                                    student = student
                                )
                                enrolment.save()
            elif student.primary_school_type == 'sjkc':
                student.sjkc_level = request.POST['sjkc_level']
                for primary_level, subjects in primary_subjects['sjkc'].items():
                    for subject in subjects:
                        selected_timeslot_id = request.POST.get(subject)
                        if selected_timeslot_id and selected_timeslot_id != "0":
                            selected_tuition_class = Tuition_Classes.objects.get(id = selected_timeslot_id)
                            if selected_tuition_class.tuition_class_study_level == f"Primary sjkc {primary_level}":
                                enrolment = Enrolment(
                                    request_type = 'Add',
                                    request_status = 'Pending',
                                    enrolment_status = 'Active',
                                    tuition_classes = selected_tuition_class,
                                    student = student
                                )
                                enrolment.save()
        elif student.school_level == 'secondary':
            student.secondary_level = request.POST['secondary_level']
            for subject in secondary_subjects[student.secondary_level]:
                selected_timeslot_id = request.POST.get(subject)
                if selected_timeslot_id and selected_timeslot_id != "0":
                    selected_tuition_class = Tuition_Classes.objects.get(id=selected_timeslot_id)
                    if selected_tuition_class.tuition_class_study_level == f"Secondary {student.secondary_level}":
                        enrolment = Enrolment(
                            request_type = 'Add',
                            request_status = 'Pending',
                            enrolment_status = 'Active',
                            tuition_classes = selected_tuition_class,
                            student = student
                        )
                        enrolment.save()

        messages.success(request, "You have successfully registered. Please login.")
        return redirect(reverse('login'))
    return render (request, "register.html", context)



def login(request):
    if request.method == 'POST':
        email = request.POST['email'].lower()  # Convert email to lowercase
        password = request.POST['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Account with this email does not exist. Please sign up.')
            return render(request, 'login.html')

        if check_password(password, user.password):  # Use check_password for secure comparison
            auth.login(request, user)
            if user.role == 'STUDENT':
                return redirect('student_tuition_classes_list')  # Redirect to the student dashboard
            elif user.role == 'SUPER ADMIN' or user.role == 'ADMIN':
                return redirect('admin_class_dashboard')
            else:
                return redirect('enquiry')
        else:
            messages.error(request, 'Incorrect password. Please try again.')
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')


def logout(request):
    if request.method == 'POST':
        auth.logout(request)
    return redirect ('login')


from django.contrib.sites.shortcuts import get_current_site

def forgot_password(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            User = get_user_model()
            user = User.objects.filter(email=email).first()
            if user:
                subject = "Password Reset Request"

                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)

                current_site = get_current_site(request)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = reverse('resetpassword', kwargs={'uidb64': uidb64, 'token': token})
                reset_url = f"http://{current_site.domain}{reset_url}"
                
                message = f"We have received a request to reset the password for your account. To complete the process, click the following link: \n\n {reset_url}"
                from_email = "annjoe01@hotmail.com" #Change this to your desired sender email
                send_mail(subject, message, from_email, [email])
                messages.success(request, "A password reset link has been sent to your email.")
            else:
                messages.error(request, "This email is not associated with any account.")
    else:
        form = PasswordResetForm()

    return render(request, "forgotpassword.html", {"form": form})


def reset_password (request, uidb64, token):
    #User = get_user_model()

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and PasswordResetTokenGenerator().check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                new_password = form.cleaned_data.get('new_password1')
                if user.check_password(new_password):
                    messages.error(request, "You cannot use your old password as the new password.")
                else:
                    form.save()
                    messages.success(request, "Your password has been successfully reset. You can log in with your new password.")
                    return redirect("login")
        else:
            form = SetPasswordForm(user)
    else:
        messages.error(request, "The password reset link you have used is invalid or has expired. You can initiate a new password reset request here.")
        return redirect ("forgotpassword")
        
    return render (request, "resetpassword.html", {"form": form, "uidb64": uidb64, "token":token})

        


def sidebar_student (request):
    return render (request, "sidebar_student.html")


@login_required
def student_changepassword (request):
    if request.method =='POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user) #Update the user's session with the new password
            messages.success(request, 'Your password was successfully update.')
            return redirect ('student_changepassword')
            
        else:
            messages.error(request, 'Your current password or new password or confirm new password is incorrect. Please try again.')

    else:
        form = PasswordChangeForm (user=request.user)
    return render(request, 'student_changepassword.html', {'form':form})
    
@login_required
def admin_changepassword (request):
    if request.method =='POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user) #Update the user's session with the new password
            messages.success(request, 'Your password was successfully update.')
            return redirect ('admin_changepassword')
            
        else:
            messages.error(request, 'Your current password or new password or confirm new password is incorrect. Please try again.')

    else:
        form = PasswordChangeForm (user=request.user)
    return render(request, 'admin_changepassword.html', {'form':form})
    


def admin_dashboard (request):
    return render(request, 'admin_dashboard.html')

def updateprofile_student(request):
    user_id = request.user.id
    user = User.objects.get(id=user_id)
    student = Student.objects.get(user_id=user_id)

    if request.method == "POST":
        user.full_name = request.POST['full_name']
       
        student.school_level = request.POST['school_level']
        if student.school_level == 'primary':
            student.primary_school_type = request.POST['primary_school_type']
            if student.primary_school_type == 'sk':
                student.sk_level = request.POST['sk_level']
            elif student.primary_school_type == 'sjkc':
                student.sjkc_level = request.POST['sjkc_level']
        elif student.school_level == 'secondary':
            student.secondary_level = request.POST['secondary_level']

        student.school_name = request.POST['school_name']
        student.startdate = request.POST['startdate']

        # Handle the new bankin_receipt uploaded file
        new_bankin_receipt = request.FILES.get('bankin_receipt')
        if new_bankin_receipt:
            username = user.full_name
            extension = os.path.splitext(new_bankin_receipt.name)[-1]
            
            # Get the count of existing bankin_receipt files
            existing_count = Student.objects.filter(bankin_receipt__icontains=username).count()

             # Create a new filename with a unique number
            new_filename = f"{username}_BankInReceipt_{existing_count + 1}{extension}"

            # Assign the new filename to the uploaded file
            #new_bankin_receipt.name = new_filename
            
            # Save the uploaded file (bankin_receipt)
            student.bankin_receipt.save(new_filename, new_bankin_receipt, save=True)
      
        student.classin_phoneno = request.POST['classin_phoneno']
        user.phone_no = request.POST['phone_no']
        student.parent_phoneno2 = request.POST['parent_phoneno2']
        student.student_phoneno = request.POST['student_phoneno']
        user.street1 = request.POST['street1']
        user.street2 = request.POST['street2']
        user.city = request.POST['city']
        user.postalcode = request.POST['postalcode']
        user.state = request.POST['state']

        user.save()
        student.save()

        messages.success(request,'Profile details updated successfully.')
        return redirect('updateprofile_student') 
    
    context={
       'user': user,
       'student': student,
       'student_bankin_receipt_name': os.path.basename(student.bankin_receipt.url),
       'student_ic_photo_name': os.path.basename(student.student_ic_photo.url),
       'student_photo_name': os.path.basename(student.student_photo.url),
    }

    return render (request, 'updateprofile_student.html', context)

def updateprofile_admin (request):
    user_id = request.user.id
    user = User.objects.get(id=user_id)
    

    if request.method == "POST":
        user.full_name = request.POST['full_name']
        user.phone_no = request.POST['phone_no']
        user.street1 = request.POST['street1']
        user.street2 = request.POST['street2']
        user.city = request.POST['city']
        user.postalcode = request.POST['postalcode']
        user.state = request.POST['state']
        user.save()
        
        messages.success(request,'Profile details updated successfully.')
        return redirect('updateprofile_admin') 

    context={
       'user': user,
    }

    return render (request, 'updateprofile_admin.html', context)

def enquiry (request):
    return render(request,'enquiry.html')

def sidebartest (request):
    return render (request, 'sidebartest.html')


def admin_student_list (request):
    # Retrieve all Student objects from the database
    student = Student.objects.all()

    # Create a paginator object with the queryset and set the number of item per page
    paginator = Paginator(student, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the page object for the current page
    page = paginator.get_page(page_number)
    
    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page -2 ), min(max_pages, current_page + 2) + 1)

    archived_students = Student.objects.filter(is_archived=True).order_by('archived_at')
    second_paginator = Paginator(archived_students, 10)
    second_page_number = request.GET.get('second_page')
    second_page = second_paginator.get_page(second_page_number)
    max_pages_second = second_paginator.num_pages
    current_page_second = second_page.number
    page_range_second = range(max(1, current_page_second - 2), min(max_pages_second, current_page_second + 2) + 1)

    context = {
        'students': page,
        'page_range': page_range,
        'archived_students': second_page,
        'page_range_second': page_range_second
    }
    return render (request, 'admin_student_list.html', context)

def addnewstudent (request):
    # Fetch all subjects from the database
    subjects = Tuition_Classes.objects.all()

    # Filter unique subjects for Kindergarten level
    kindergarten_subjects = set()
    for subject in subjects:
        if subject.tuition_class_study_level == "Kindergarten":
            kindergarten_subjects.add(subject.subject)

    primary_subjects = {
        'sk':{
            'std1': set(),
            'std2': set(),
            'std3': set(),
            'std4': set(),
            'std5': set(),
            'std6': set(),
        },
        'sjkc':{
            'std1': set(),
            'std2': set(),
            'std3': set(),
            'std4': set(),
            'std5': set(),
            'std6': set(),
        }
    }

    for subject in subjects:
        if subject.tuition_class_study_level.startswith("Primary"):
            components = subject.tuition_class_study_level.split()
            school_type = components[1]
            primary_level = components[2]

            if school_type == 'sk':
                primary_subjects['sk'][primary_level].add(subject.subject)
            elif school_type == 'sjkc':
                primary_subjects['sjkc'][primary_level].add(subject.subject)

    secondary_subjects = {
        'form1': set(),
        'form2': set(),
        'form3': set(),
        'form4': set(),
        'form5': set(),
    }

    for subject in subjects:
        if subject.tuition_class_study_level.startswith("Secondary"):
            components = subject.tuition_class_study_level.split()
            secondary_level=components[1]

            secondary_subjects[secondary_level].add(subject.subject)

    context = {
        'subjects': subjects,
        'kindergarten_subjects': kindergarten_subjects,
        'primary_subjects': primary_subjects,
        'secondary_subjects': secondary_subjects,

    }

    if request.method == 'POST':
        email = request.POST['email']

        # Checkif a user with this email already exists
        try: 
            existing_user = User.objects.get(email=email)
            messages.error(request, 'An account with this email already exists. Please login.')
            return render (request,'addnewstudent.html', {'message':'An account with this email already exists. Please choose a different email.'})
        except User.DoesNotExist:
            pass

         # Create a new user object
        new_user = User()
        new_user.full_name = request.POST['fullname']
        new_user.email=email
        new_user.password = make_password(request.POST['password'])
        new_user.role = 'STUDENT' # set all the new user's role as student
        # Create a new student object with user as foreign key
        student = Student()
        student.user = new_user

        student.school_level = request.POST['school_level']
        if student.school_level == 'primary':
            student.primary_school_type = request.POST['primary_school_type']
            if student.primary_school_type == 'sk':
                student.sk_level = request.POST['sk_level']
            elif student.primary_school_type == 'sjkc':
                student.sjkc_level = request.POST['sjkc_level']
        elif student.school_level == 'secondary':
            student.secondary_level = request.POST['secondary_level']
        
        student.school_name = request.POST['school_name']
        student.startdate = datetime.strptime(request.POST['startdate'], '%Y-%m-%d').date()
        
        # Handle the bankin_receipt uploaded file
        bankin_receipt = request.FILES.get('bankin_receipt')
        if bankin_receipt:

            # Generate a new filename based on the user's username
            username = new_user.full_name
            extension = os.path.splitext(bankin_receipt.name)[-1]
            new_filename = f"{username}_BankInReceipt{extension}"

            #Assign the new filename to the uploaded file
            bankin_receipt.name = new_filename
            
            # Save the uploaded file (bankin_receipt)
            student.bankin_receipt = bankin_receipt

        student.classin_phoneno = request.POST['classin_phoneno']
        new_user.phone_no = request.POST['phoneNo'] 
        student.parent_phoneno2 = request.POST['parent_phoneno2']
        student.student_phoneno = request.POST['student_phoneno']

        student.student_ic_number = request.POST['student_ic_number']
       
        # Handle the student_ic_photo uploaded file
        ic_photo = request.FILES.get('student_ic_photo')
        if ic_photo:
            
            # Geerate a new filename based on the user's username
            username = new_user.full_name
            extension = os.path.splitext(ic_photo.name)[-1]
            new_filename = f"{username}_IcPhoto{extension}"

            # Assign the new filename to the uploaded file
            ic_photo.name = new_filename

            # Save the uploaded file (ic_photo)
            student.student_ic_photo = ic_photo

        # Handle the student_photo uploaded file
        student_photo = request.FILES.get('student_photo')
        if student_photo:

            # Generate a new filename based on the user's username
            username = new_user.full_name
            extension = os.path.splitext(student_photo.name)[-1]
            new_filename = f"{username}_StudentPhoto{extension}"

            # Assign the new filename to the uploaded file
            student_photo.name = new_filename
            
            # Save the uploaded file (student_photo)
            student.student_photo = student_photo
        
        new_user.street1 = request.POST['street1']
        new_user.street2 = request.POST['street2']
        new_user.city = request.POST['city']
        new_user.postalcode = request.POST['postalcode']
        new_user.state = request.POST['state']

        # know us from field
        selected_options=[]
        if 'facebook' in request.POST:
            selected_options.append('Facebook')
        if 'instagram' in request.POST:
            selected_options.append('Instagram')
        if 'google' in request.POST:
            selected_options.append('Google')
        if 'tiktok' in request.POST:
            selected_options.append('Tik Tok')
        if 'friend' in request.POST:
            selected_options.append('Friend')
        if 'xhs' in request.POST:
            selected_options.append('小红书')
        if 'sibling' in request.POST:
            selected_options.append('Sibling or Family Member')

        if 'other' in request.POST:
            other_know_us_from = request.POST.get('displayOther','')
            if other_know_us_from:
                selected_options.append(other_know_us_from)

        know_us_from =','.join(selected_options)
        student.know_us_from = know_us_from
        
        new_user.save()
        student.save()

        # Now that user and student attribute are set, create enrolment if applicable
        if student.school_level == 'kindergarten':
            for subject in kindergarten_subjects:
                selected_timeslot_id = request.POST.get(subject)
                if selected_timeslot_id and selected_timeslot_id != "0": # Check for not enrolling
                    selected_tuition_class = Tuition_Classes.objects.get(id=selected_timeslot_id)
                    if selected_tuition_class.tuition_class_study_level == "Kindergarten":
                        enrolment = Enrolment(
                            request_type = 'Add',
                            request_status = 'Pending',
                            enrolment_status = 'Active',
                            tuition_classes = selected_tuition_class,
                            student = student
                        )
                        enrolment.save()
        elif student.school_level == 'primary':
            student.primary_school_type = request.POST['primary_school_type']
            if student.primary_school_type == 'sk':
                student.sk_level = request.POST['sk_level']
                for primary_level, subjects in primary_subjects['sk'].items():
                    for subject in subjects:
                        selected_timeslot_id = request.POST.get(subject)
                        if selected_timeslot_id and selected_timeslot_id != "0":
                            selected_tuition_class = Tuition_Classes.objects.get(id = selected_timeslot_id)
                            if selected_tuition_class.tuition_class_study_level == f"Primary sk {primary_level}":
                                enrolment = Enrolment(
                                    request_type = 'Add',
                                    request_status = 'Pending',
                                    enrolment_status = 'Active',
                                    tuition_classes = selected_tuition_class,
                                    student = student
                                )
                                enrolment.save()
            elif student.primary_school_type == 'sjkc':
                student.sjkc_level = request.POST['sjkc_level']
                for primary_level, subjects in primary_subjects['sjkc'].items():
                    for subject in subjects:
                        selected_timeslot_id = request.POST.get(subject)
                        if selected_timeslot_id and selected_timeslot_id != "0":
                            selected_tuition_class = Tuition_Classes.objects.get(id = selected_timeslot_id)
                            if selected_tuition_class.tuition_class_study_level == f"Primary sjkc {primary_level}":
                                enrolment = Enrolment(
                                    request_type = 'Add',
                                    request_status = 'Pending',
                                    enrolment_status = 'Active',
                                    tuition_classes = selected_tuition_class,
                                    student = student
                                )
                                enrolment.save()
        elif student.school_level == 'secondary':
            student.secondary_level = request.POST['secondary_level']
            for subject in secondary_subjects[student.secondary_level]:
                selected_timeslot_id = request.POST.get(subject)
                if selected_timeslot_id and selected_timeslot_id != "0":
                    selected_tuition_class = Tuition_Classes.objects.get(id=selected_timeslot_id)
                    if selected_tuition_class.tuition_class_study_level == f"Secondary {student.secondary_level}":
                        enrolment = Enrolment(
                            request_type = 'Add',
                            request_status = 'Pending',
                            enrolment_status = 'Active',
                            tuition_classes = selected_tuition_class,
                            student = student
                        )
                        enrolment.save()

        messages.success(request, "New student has successfully added.")
        return redirect('student_list_view')
    return render (request, "addnewstudent.html", context)

def view_student_detail (request,pk):
    student = get_object_or_404(Student, pk=pk)

    #Filter enrollments related to student 
    student_enrollments = Enrolment.objects.filter(student=student)

    # Retrieve the 'Add' enrolments with 'Accepted' status for the student
    add_enrolments = Enrolment.objects.filter(
        request_type = 'Add',
        request_status = 'Accepted',
        student = student
    )

    # Create a list of vlass IDs for which 'Drop' requests have been accepeted
    drop_classes = set()
    for enrolment in add_enrolments:
        drop_enrolments = Enrolment.objects.filter(
            request_type = 'Drop',
            request_status = 'Accepted',
            tuition_classes = enrolment.tuition_classes
        ).first()

        if drop_enrolments:
            drop_classes.add(enrolment.tuition_classes_id)
    
    # Filter classes to display 
    classes_enrolled = add_enrolments.exclude(tuition_classes__id__in=drop_classes)
    active_tab = request.GET.get('active_tab')
    paginator = Paginator(classes_enrolled, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page -2), min(max_pages, current_page + 2) + 1)

    added_enrolments = Enrolment.objects.filter(
        Q(request_type = 'Add') & (Q(request_status = 'Accepted') | Q(request_status = 'Rejected')), student = student
    ).order_by('-request_responded_at')

    dropped_enrolments = Enrolment.objects.filter(
        Q(request_type = 'Drop') & (Q(request_status = 'Accepted') | Q(request_status = 'Rejected')), student = student
    ).order_by('-request_responded_at')

    enrolment_requests = Enrolment.objects.filter(student=student, request_status ='Pending')
    second_paginator = Paginator(enrolment_requests, 1)
    second_page_number = request.GET.get('second_page')
    second_page = second_paginator.get_page(second_page_number)
    max_pages_second = second_paginator.num_pages
    current_page_second = second_page.number
    page_range_second = range(max(1, current_page_second - 2), min(max_pages_second, current_page_second + 2) + 1)
    
    # Filter evaluations created by the respective student
    student_evaluations = Subject_Evaluation.objects.filter(student=student)

    context={
       'student': student,
       'student_bankin_receipt_name': os.path.basename(student.bankin_receipt.url),
       'student_ic_photo_name': os.path.basename(student.student_ic_photo.url),
       'student_photo_name': os.path.basename(student.student_photo.url),
       'student_enrollments': student_enrollments,
       'classes_enrolled': page,
       'page_range': page_range,
        'added_enrolments': added_enrolments,
        'dropped_enrolments': dropped_enrolments,
        'student_evaluations': student_evaluations,
        'enrolment_requests': second_page,
        'page_range_second': page_range_second,
        'active_tab': active_tab,
    }
    return render (request, 'view_student_detail.html', context)



def edit_student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    user=student.user

    # Retrieve the active_tab parameter from the query string
    active_tab = request.GET.get('active_tab')

    # Fetch all subjects from the database
    subjects = Tuition_Classes.objects.all()

    #Filter enrollments related to student 
    student_enrollments = Enrolment.objects.filter(student=student)

    # Retrieve the 'Add' enrolments with 'Accepted' status for the student
    add_enrolments = Enrolment.objects.filter(
        request_type = 'Add',
        request_status = 'Accepted',
        student = student
    )

    # Create a list of vlass IDs for which 'Drop' requests have been accepeted
    drop_classes = set()
    for enrolment in add_enrolments:
        drop_enrolments = Enrolment.objects.filter(
            request_type = 'Drop',
            request_status = 'Accepted',
            tuition_classes = enrolment.tuition_classes
        ).first()

        if drop_enrolments:
            drop_classes.add(enrolment.tuition_classes_id)
    
    # Filter classes to display 
    classes_enrolled = add_enrolments.exclude(tuition_classes__id__in=drop_classes)
    active_tab = request.GET.get('active_tab')
    paginator = Paginator(classes_enrolled, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page -2), min(max_pages, current_page + 2) + 1)

    added_enrolments = Enrolment.objects.filter(
        Q(request_type = 'Add') & (Q(request_status = 'Accepted') | Q(request_status = 'Rejected')), student = student
    ).order_by('-request_responded_at')

    dropped_enrolments = Enrolment.objects.filter(
        Q(request_type = 'Drop') & (Q(request_status = 'Accepted') | Q(request_status = 'Rejected')), student = student
    ).order_by('-request_responded_at')

    enrolment_requests = Enrolment.objects.filter(student=student, request_status ='Pending')
    
    # Filter evaluations created by the respective student
    student_evaluations = Subject_Evaluation.objects.filter(student=student)



    # Filter unique subjects for Kindergarten level
    kindergarten_subjects = set()
    for subject in subjects:
        if subject.tuition_class_study_level == "Kindergarten":
            kindergarten_subjects.add(subject.subject)

    primary_subjects = {
        'sk':{
            'std1': set(),
            'std2': set(),
            'std3': set(),
            'std4': set(),
            'std5': set(),
            'std6': set(),
        },
        'sjkc':{
            'std1': set(),
            'std2': set(),
            'std3': set(),
            'std4': set(),
            'std5': set(),
            'std6': set(),
        }
    }

    for subject in subjects:
        if subject.tuition_class_study_level.startswith("Primary"):
            components = subject.tuition_class_study_level.split()
            school_type = components[1]
            primary_level = components[2]

            if school_type == 'sk':
                primary_subjects['sk'][primary_level].add(subject.subject)
            elif school_type == 'sjkc':
                primary_subjects['sjkc'][primary_level].add(subject.subject)

    secondary_subjects = {
        'form1': set(),
        'form2': set(),
        'form3': set(),
        'form4': set(),
        'form5': set(),
    }

    for subject in subjects:
        if subject.tuition_class_study_level.startswith("Secondary"):
            components = subject.tuition_class_study_level.split()
            secondary_level=components[1]

            secondary_subjects[secondary_level].add(subject.subject)


    if request.method == "POST":
        user.full_name = request.POST['full_name']

        student.school_level = request.POST['school_level']
        if student.school_level == 'primary':
            student.primary_school_type = request.POST['primary_school_type']
            if student.primary_school_type == 'sk':
                student.sk_level = request.POST['sk_level']
            elif student.primary_school_type == 'sjkc':
                student.sjkc_level = request.POST['sjkc_level']
        elif student.school_level == 'secondary':
            student.secondary_level = request.POST['secondary_level']

        student.school_name = request.POST['school_name']
        student.startdate = request.POST['startdate']
        
        # Handle the new bankin_receipt uploaded file
        new_bankin_receipt = request.FILES.get('bankin_receipt')
        if new_bankin_receipt:
            username = user.full_name
            extension = os.path.splitext(new_bankin_receipt.name)[-1]
            
            # Get the count of existing bankin_receipt files
            existing_count = Student.objects.filter(bankin_receipt__icontains=username).count()

             # Create a new filename with a unique number
            new_filename = f"{username}_BankInReceipt_{existing_count + 1}{extension}"

            # Assign the new filename to the uploaded file
            #new_bankin_receipt.name = new_filename
            
            # Save the uploaded file (bankin_receipt)
            student.bankin_receipt.save(new_filename, new_bankin_receipt, save=True)

        student.classin_phoneno = request.POST['classin_phoneno']
        user.phone_no = request.POST['phoneNo']
        student.parent_phoneno2 = request.POST['parent_phoneno2']
        student.student_phoneno = request.POST['student_phoneno']
        user.street1 = request.POST['street1']
        user.street2 = request.POST['street2']
        user.city = request.POST['city']
        user.postalcode = request.POST['postalcode']
        user.state = request.POST['state']

        user.save()
        student.save()

        messages.success(request,'The changes have been successfully updated.')
        return redirect(reverse('edit_student_detail',args=[pk]))
    

    context={
        'user': user,
        'student': student,
        'student_bankin_receipt_name': os.path.basename(student.bankin_receipt.url),
        'student_ic_photo_name': os.path.basename(student.student_ic_photo.url),
        'student_photo_name': os.path.basename(student.student_photo.url),
        'student_enrollments': student_enrollments,
        'subjects': subjects,
        'kindergarten_subjects': kindergarten_subjects,
        'primary_subjects': primary_subjects,
        'secondary_subjects': secondary_subjects,
        'active_tab': active_tab,
        'classes_enrolled': page,
        'page_range': page_range,
        'added_enrolments': added_enrolments,
        'dropped_enrolments': dropped_enrolments,
        'student_evaluations': student_evaluations,
        'enrolment_requests': enrolment_requests,
    }
    
    
    return render(request, 'edit_student_detail.html', context)




def delete_student(request, pk):

    #Retrieve the student object
    student = get_object_or_404(Student, id=pk)

    # Delete the associated user object
    student.user.delete()
    return redirect('student_list_view')

def event_detail(request):
    return render (request, 'event_detail.html')

@login_required
def admin_list_view (request):
    #Retrieve all User objects with the role 'ADMIN' from the database
    admins = User.objects.filter(role='ADMIN').order_by('created_at')

    # Create a paginator object with the queryset and set the number of items per page
    paginator = Paginator(admins,10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the page object for the current page
    page = paginator.get_page(page_number)

    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page-2), min(max_pages, current_page + 2) + 1)

    context ={
        'users': page,
        'page_range': page_range,
    }
     
    #Pass the admins queryset to the template for rendering
    return render (request, 'admin_list_view.html', context)

def view_admin_detail (request,pk):
    user = get_object_or_404(User, pk=pk, role='ADMIN')
    return render (request, 'view_admin_detail.html', {'user': user})

def edit_admin_detail(request,pk):
    user = get_object_or_404(User, id=pk, role='ADMIN')

    if request.method == "POST":
        user.full_name = request.POST['full_name']
        
        user.phone_no = request.POST['phoneNo']
        user.street1 = request.POST['street1']
        user.street2 = request.POST['street2']
        user.city = request.POST['city']
        user.postalcode = request.POST['postalcode']
        user.state = request.POST['state']
        user.save()

        messages.success(request,'The changes have been successfully updated.')
        return redirect ('edit_admin_detail', pk=user.id)
    
    return render (request, 'edit_admin_detail.html', {'user': user})

def addnewadmin (request):
    if request.method == 'POST':
        email = request.POST['email']

        try: 
            existing_user = User.objects.get(email=email)
            return render (request,'addnewadmin.html', {'message':'An account with this email already exists. Please choose a different email.'})
        except User.DoesNotExist:
            pass

         # Create a new user object
        new_user = User()
        new_user.full_name = request.POST['fullname']
        new_user.password = make_password(request.POST['password'])
        new_user.email=email
        new_user.phone_no = request.POST['phoneNo'] 
        new_user.role = 'ADMIN' 
        new_user.street1 = request.POST['street1']
        new_user.street2 = request.POST['street2']
        new_user.city = request.POST['city']
        new_user.postalcode = request.POST['postalcode']
        new_user.state = request.POST['state']
        new_user.save()

        #Create a new admin object and link it to the user
        #admin = Admin.objects.create(user=new_user)
        admin = Admin(user=new_user)
        admin.save()
    

        return redirect('admin_list_view')
    return render (request, "addnewadmin.html")

def delete_admin(request, pk):

    #Retrieve the student object
    user = get_object_or_404(User, id=pk, role='ADMIN')

    # Delete the associated user object
    user.delete()
    return redirect('admin_list_view')

@login_required
def admin_announcementList(request):
    user = request.user
    announcements = None

    if user.role == 'SUPER ADMIN':
        announcements = Announcement.objects.filter(Q(targeted_group='ADMIN') | Q(targeted_group='ALL')).order_by('-announcement_posted_at')
    elif user.role == 'ADMIN':
        announcements = Announcement.objects.filter(Q(targeted_group='ADMIN') | Q(targeted_group='ALL')).order_by('-announcement_posted_at')
    elif user.role == 'STUDENT':
        announcements = Announcement.objects.filter(Q(targeted_group='STUDENT') | Q(targeted_group='ALL')).order_by('-announcement_posted_at')

    # Create a paginator object with the queryset and set the number of item per page
    paginator = Paginator(announcements, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the page object for the current page
    page = paginator.get_page(page_number)

    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)

    context = {
        'announcements': page,
        'page_range': page_range,
    }

    if user.role == 'SUPER ADMIN' or user.role == 'ADMIN':
        return render(request, 'admin_announcementList.html', context)
    elif user.role == 'STUDENT':
        return render(request,'student_announcementList.html', context)
    
    return render(request,'admin_announcementList.html', context)


def add_announcement(request):
    if request.method == 'POST':
        targeted_group = request.POST.get('targeted_group', None)
        title= request.POST.get('announcement_title', None)
        content = request.POST.get('announcement_content', None)

        # Check if all required fields are filled
        if targeted_group and title and content:
            # Save the announcement to the database
            announcement = Announcement(
                targeted_group = targeted_group,
                announcement_title = title,
                announcement_content = content,
                announcement_posted_by = request.user
            )
            announcement.save()
            messages.success(request, 'The announcement has been successfully published.')
            return redirect('admin_sentAnnouncementList')
    return render (request,"admin_sentAnnouncementList.html")

def display_announcement_superadmin(request, announcement_id):
    announcement = get_object_or_404(Announcement, pk=announcement_id)
    return render (request, 'display_announcement.html',{'announcement': announcement})

def admin_sentAnnouncementList(request):
    user = request.user
    announcements = None

    if user.role == 'SUPER ADMIN':
        announcements = Announcement.objects.all().order_by('-announcement_posted_at')
    elif user.role == 'ADMIN':
        announcements = Announcement.objects.filter(announcement_posted_by__user=user).order_by('-announcement_posted_at')

    # Create a paginator object with the queryset and set the number of item per page
    paginator = Paginator(announcements, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the oage object for the current page
    page = paginator.get_page(page_number)

    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)

    context = {
        'announcements': page,
        'page_range': page_range,
    }

    if user.role == 'SUPER ADMIN' or user.role == 'ADMIN':
        return render(request, 'admin_sentAnnouncementList.html', context)
    
    return render(request,'admin_sentAnnouncementList.html',context)



def calendar_view (request):
    all_events = Calendar_Events.objects.all()

    context={
        'events': all_events,
    }

    return render(request,'calendar.html',context)

def all_events(request):
    all_events = Calendar_Events.objects.all()
    out = []
    for event in all_events:
        out.append({
            'title': event.event_name,
            'id': event.id,
            'start': event.start_date.strftime("%m/%d/%Y, %H:%M:%S"), 
            'end': event.end_date.strftime("%m/%d/%Y, %H:%M:%S"), 
            'color': get_event_color(event.event_type)
        })
    return JsonResponse(out, safe=False)

def get_event_color(event_type):
    color_map = {
        'event': '#3788D8', # Blue colour
        'holiday': '#588A71', # Green colour
        'meeting': '#F39C12' # Orange colour
    }
    return color_map.get(event_type,'#3788D8')

def add_event(request):
    if request.method == 'POST':
        event_name = request.POST['event_name']
        event_type = request.POST['event_type']
        event_description = request.POST['event_description']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']

        # Create a new event object and save it to the database
        event = Calendar_Events(
            event_name = event_name,
            event_type = event_type,
            event_description = event_description,
            start_date = start_date,
            end_date = end_date
        )
        event.save()

        messages.success(request,"Event added successfully.")
        return redirect('calendar')
  
    return render(request, 'add_event_template.html')

def update_event(request, event_id):
    event = get_object_or_404(Calendar_Events, pk=event_id)

    if request.method == "POST":
        event.event_name = request.POST['event_name']
        event.event_type = request.POST['event_type']
        event.event_description = request.POST['event_description']
        event.start_date = request.POST['start_date']
        event.end_date = request.POST['end_date']

        event.save()

        messages.success(request,"Event details updated successfully.")
        return redirect('calendar')

    return redirect('calendar', event=event) #Pass the context data correctly

def delete_event(request, event_id):
    event = get_object_or_404(Calendar_Events, pk=event_id)

    if request.method == "POST":
        event.delete()

        messages.success(request, "Event deleted successfully.")
        return redirect('calendar') # Redirect to the calendar view
    
    return redirect('calendar') # Redirect if not a POST request


def edit_student_detail_enrolment(request, pk):
    
        # Fetch all subjects from the database
        subjects = Tuition_Classes.objects.all()

        # Filter unique subjects for Kindergarten level
        kindergarten_subjects = set()
        for subject in subjects:
            if subject.tuition_class_study_level == "Kindergarten":
                kindergarten_subjects.add(subject.subject)

        # Get the student object based on student_id
        student = get_object_or_404(Student, id=pk)
        
        # Filter enrollments related to student 
        student_enrollments = Enrolment.objects.filter(student=student)

        context = {
            'subjects': subjects,
            'kindergarten_subjects': kindergarten_subjects,
            'student': student,
            'student_enrollments': student_enrollments,
        }

        return render(request, 'edit_student_detail.html', context)
   
def add_enrolment(request,pk):
    student = get_object_or_404(Student, id=pk)

    # Set the active tab to "tab2" 
    active_tab = "tab2"

    # Fetch all subjects from the database
    subjects = Tuition_Classes.objects.all()

    # Create an empty dictionary to store subject-to-timeslot mappings
    subject_to_timeslot = {}

    for subject in subjects:
        selected_timeslot_id = request.POST.get(subject.subject)
        if selected_timeslot_id and selected_timeslot_id != "0":
            subject_to_timeslot[subject.subject] = selected_timeslot_id

    # Create enrolments based on subject-to-timeslot mappings
    for subject, timeslot_id in subject_to_timeslot.items():
        selected_tuition_class = Tuition_Classes.objects.get(id=timeslot_id)
        enrolment = Enrolment(
            request_type = 'Add',
            request_status = 'Pending',
            enrolment_status = 'Active',
            tuition_classes = selected_tuition_class,
            student = student
        )
        enrolment.save()
    
    messages.success(request,"New enrolment(s) have been successfully added.")
    return redirect(reverse('edit_student_detail', args=[pk]) + f'?active_tab={active_tab}')

def admin_enrolment_request(request):

    # Retrieve entolment requests with related data
    enrolment_requests = Enrolment.objects.filter(request_status='Pending').order_by('request_created_at')

    # Create a paginator object with the queryset and set the number of items per page
    paginator = Paginator(enrolment_requests, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the page object for the current page
    page = paginator.get_page(page_number)

    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page-2), min(max_pages, current_page + 2) + 1)

    context ={
        'enrolment_requests': page,
        'page_range': page_range,
    }

    return render(request,'admin_enrolment_request.html',context)

def accept_enrolment(request, request_id):

    # Get the enrolment request
    enrolment_request = get_object_or_404(Enrolment, id=request_id)

    if enrolment_request.request_type == 'Add':
        # Handle the 'Add' request
        # Update the attribute of Enrolment
        enrolment_request.request_status = 'Accepted'
        enrolment_request.enrolment_status = 'Active'
        enrolment_request.request_responded_at = timezone.now()
        enrolment_request.enrol_at = enrolment_request.request_responded_at

        # Save the changes to the database
        enrolment_request.save()
        
        return redirect('admin_enrolment_request')
    
    elif enrolment_request.request_type == 'Drop':
        # Handle the 'Drop' request
        # Update the attribute of Enrolment for the drop request
        enrolment_request.request_status = 'Accepted'
        enrolment_request.enrolment_status = 'Dropped'
        enrolment_request.request_responded_at = timezone.now()
        enrolment_request.is_stop = True
        enrolment_request.stop_at = enrolment_request.request_responded_at

        enrolment_request.save()

        return redirect('admin_enrolment_request')

def reject_enrolment(request, request_id):

    # Get the enrolment request
    enrolment_request = get_object_or_404(Enrolment, id=request_id)

    if enrolment_request.request_type == 'Add':
        # Handle the 'Add' request
        # Update the attribute of Enrolment
        enrolment_request.request_status = 'Rejected'
        enrolment_request.enrolment_status = 'Not Admitted'
        enrolment_request.request_responded_at = timezone.now()
        enrolment_request.enrol_at = enrolment_request.request_responded_at

        # Save the changes to the database
        enrolment_request.save()
        
        return redirect('admin_enrolment_request')
    
    elif enrolment_request.request_type == 'Drop':
        # Handle the 'Drop' request
        # Update the attribute of Enrolment for the drop request
        enrolment_request.request_status = 'Rejected'
        enrolment_request.enrolment_status = 'Active'
        enrolment_request.request_responded_at = timezone.now()

        enrolment_request.save()

        return redirect('admin_enrolment_request')

def student_enrolment_request(request):

    # Retrieve the logged-in user 
    user = request.user
    student = Student.objects.get(user=user)
    
    enrolment_requests = Enrolment.objects.filter(student=student, request_status='Pending')

    # Fetch all subjects from the database
    subjects = Tuition_Classes.objects.all()

    # Filter unique subjects for Kindergarten level
    kindergarten_subjects = set()
    for subject in subjects:
        if subject.tuition_class_study_level == "Kindergarten":
            kindergarten_subjects.add(subject.subject)

    primary_subjects = {
        'sk':{
            'std1': set(),
            'std2': set(),
            'std3': set(),
            'std4': set(),
            'std5': set(),
            'std6': set(),
        },
        'sjkc':{
            'std1': set(),
            'std2': set(),
            'std3': set(),
            'std4': set(),
            'std5': set(),
            'std6': set(),
        }
    }

    for subject in subjects:
        if subject.tuition_class_study_level.startswith("Primary"):
            components = subject.tuition_class_study_level.split()
            school_type = components[1]
            primary_level = components[2]

            if school_type == 'sk':
                primary_subjects['sk'][primary_level].add(subject.subject)
            elif school_type == 'sjkc':
                primary_subjects['sjkc'][primary_level].add(subject.subject)

    secondary_subjects = {
        'form1': set(),
        'form2': set(),
        'form3': set(),
        'form4': set(),
        'form5': set(),
    }

    for subject in subjects:
        if subject.tuition_class_study_level.startswith("Secondary"):
            components = subject.tuition_class_study_level.split()
            secondary_level=components[1]

            secondary_subjects[secondary_level].add(subject.subject)


    # Create a paginator object with the queryset and set the number of item per page
    paginator = Paginator(enrolment_requests, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the page object for the current page
    page = paginator.get_page(page_number)

    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)

    context = {
        'user': user,
        'student': student,
        'enrolment_requests': page,
        'page_range': page_range,
        'subjects': subjects,
        'kindergarten_subjects': kindergarten_subjects,
        'primary_subjects': primary_subjects,
        'secondary_subjects': secondary_subjects,
    }

    return render (request, 'student_enrolment_request.html', context)

def student_delete_enrolment_request(request, request_id):
    # Get the enrolment request to delete
    enrolment_request = get_object_or_404(Enrolment, id=request_id)

    # Check if the request belongs to the logged-in user (you can customize this logic)
    if enrolment_request.student.user != request.user:
        # Handle unauthorized deletion here, e.g., return an error page or redirect
        pass

    # Delete the enrolment request
    enrolment_request.delete()

    messages.success(request,'The enrolment request(s)have been successfully deleted.')
    # Redirect to a success page or a relevant URL
    return redirect('student_enrolment_request')

def admin_tuition_classes_list(request):

    # Retrieve tuition classes with its respective data
    tuition_classes = Tuition_Classes.objects.filter(is_archived=False).order_by('created_at')

    # Retrieve the active tab parameter from the query string
    active_tab = request.GET.get('active_tab')

    # Create a paginator object with the queryset and set the number of item per pafe
    paginator = Paginator(tuition_classes, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the page object for the current page
    page = paginator.get_page(page_number)

    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)

    # Retrieve archived tuition classes with its respective data
    archived_tuition_classes = Tuition_Classes.objects.filter(is_archived=True).order_by('archived_at')
    second_paginator = Paginator(archived_tuition_classes, 10)
    second_page_number = request.GET.get('second_page')
    second_page = second_paginator.get_page(second_page_number)
    max_pages_second = second_paginator.num_pages
    current_page_second = second_page.number
    page_range_second = range(max(1, current_page_second - 2), min(max_pages_second, current_page_second + 2) + 1)


    context={
        'tuition_classes':page,
        'page_range': page_range,
        'archived_tuition_classes': second_page,
        'page_range_second': page_range_second,
        'active_tab': active_tab,
    }
    return render(request, 'admin_tuition_classes_list.html',context)

def admin_archive_class (request,pk):
    archive_class = get_object_or_404(Tuition_Classes, id=pk)

    # Set the active tab to "tab2"
    active_tab = "tab2"

    archive_class.is_archived = True
    archive_class.archived_at = timezone.now()
    archive_class.unarchived_at = None # Reset the unarchive timestamp to None
    archive_class.save()


    messages.success(request, 'The class is successfully archived.')
    return redirect(f'/admin_tuition_classes_list/?active_tab={active_tab}')

def admin_unarchive_class(request,pk):
    unarchive_class = get_object_or_404(Tuition_Classes, id=pk)
    
    # Set the active tab to "tab1"
    active_tab = "tab1"

    if unarchive_class.is_archived:
        unarchive_class.is_archived = False
        unarchive_class.unarchived_at = timezone.now()
        unarchive_class.save()

    messages.success(request, 'The class is successfully unarchived.')
    return redirect(f'/admin_tuition_classes_list/?active_tab={active_tab}')


def admin_add_class(request):
    if request.method == 'POST':
        tuition_class_name = request.POST['class_name']
        subject = request.POST['subject']
        tutor_name = request.POST['tutor_name']
        tuition_class_study_level = request.POST['study_level']
        monthly_fee = request.POST['monthly_fee']
        weekly_day = request.POST['weekly_day']
        general_start_time = request.POST['start_time']
        general_end_time = request.POST['end_time']
        class_start_date = request.POST['start_date']
        class_end_date = request.POST['end_date']

        # Get the currently logged-in admin user
        admin_user = Admin.objects.get(user=request.user)

        # Create a new class object and save it to the database
        tuition_class = Tuition_Classes(
            tuition_class_name = tuition_class_name,
            subject = subject,
            tutor_name = tutor_name,
            tuition_class_study_level = tuition_class_study_level,
            monthly_fee = monthly_fee,
            weekly_day = weekly_day,
            general_start_time = general_start_time,
            general_end_time = general_end_time,
            class_start_date = class_start_date,
            class_end_date = class_end_date,
            admin = admin_user,
        )
        tuition_class.save()

        messages.success(request,"Class added successfully.")
        return redirect('admin_tuition_classes_list')
    return render(request, 'admin_tuition_classes_list')


def admin_delete_tuition_class(request, pk):
    # Get the enrolment request to delete
    tuition_classes = get_object_or_404(Tuition_Classes, id=pk)

    # Delete the enrolment request
    tuition_classes.delete()

    messages.success(request,'The class(es)have been successfully deleted.')

    # Redirect to a success page or a relevant URL
    return redirect('admin_tuition_classes_list')

def admin_edit_class_detail(request,pk):
    tuition_classes = get_object_or_404(Tuition_Classes, id=pk)

    # Retrieve the active_tab parameter from the query string
    active_tab = request.GET.get('active_tab')

    if request.method == 'POST':
        tuition_classes.tuition_class_name = request.POST['class_name']
        tuition_classes.subject = request.POST['subject']
        tuition_classes.tutor_name = request.POST['tutor_name']
        tuition_classes.tuition_class_study_level = request.POST['study_level']
        tuition_classes.monthly_fee = request.POST['monthly_fee']
        tuition_classes.weekly_day = request.POST['weekly_day']
        tuition_classes.general_start_time = request.POST['start_time']
        tuition_classes.general_end_time = request.POST['end_time']
        tuition_classes.class_start_date = request.POST['start_date']
        tuition_classes.class_end_date = request.POST['end_date']

        tuition_classes.save()

        messages.success(request,'The changes have been successfully updated.')  
        return redirect(reverse('admin_edit_class_detail',args=[pk]))

    context={
        'tuition_classes':tuition_classes,
        'active_tab': active_tab,
    }

    return render(request,'admin_edit_class_detail.html', context)

def admin_view_class_detail(request,pk):
    tuition_classes = get_object_or_404(Tuition_Classes, id=pk)

    context={
        'tuition_classes': tuition_classes,
    }

    return render(request,'admin_view_class_detail.html',context)

def student_add_enrolment(request,pk):
    student = get_object_or_404(Student, id=pk)

    # Fetch all subjects from the database
    subjects = Tuition_Classes.objects.all()

    # Create an empty dictionary to store subject-to-timeslot mappings
    subject_to_timeslot = {}

    for subject in subjects:
        selected_timeslot_id = request.POST.get(subject.subject)
        if selected_timeslot_id and selected_timeslot_id != "0":
            subject_to_timeslot[subject.subject] = selected_timeslot_id

    # Create enrolments based on subject-to-timeslot mappings
    for subject, timeslot_id in subject_to_timeslot.items():
        selected_tuition_class = Tuition_Classes.objects.get(id=timeslot_id)
        enrolment = Enrolment(
            request_type = 'Add',
            request_status = 'Pending',
            enrolment_status = 'Active',
            tuition_classes = selected_tuition_class,
            student = student
        )
        enrolment.save()
    
    messages.success(request,"New enrolment(s) have been successfully added.")
    return redirect(reverse('student_enrolment_request'))


def student_tuition_classes_list(request):
    # Retrieve the logged-in user 
    user = request.user
    student = Student.objects.get(user=user)

    # Retrieve the 'Add' enrolments with 'Accepted' status for the student
    add_enrolments = Enrolment.objects.filter(
        request_type = 'Add',
        request_status = 'Accepted',
        student = student
    )

    # Create a list of vlass IDs for which 'Drop' requests have been accepeted
    drop_classes = set()
    for enrolment in add_enrolments:
        drop_enrolments = Enrolment.objects.filter(
            request_type = 'Drop',
            request_status = 'Accepted',
            tuition_classes = enrolment.tuition_classes
        ).first()

        if drop_enrolments:
            drop_classes.add(enrolment.tuition_classes_id)
    
    # Filter classes to display 
    classes_enrolled = add_enrolments.exclude(
        tuition_classes__id__in=drop_classes,
    )

    added_enrolments = Enrolment.objects.filter(
        Q(request_type = 'Add') & (Q(request_status = 'Accepted') | Q(request_status = 'Rejected')), student = student
    ).order_by('-request_responded_at')

    dropped_enrolments = Enrolment.objects.filter(
        Q(request_type = 'Drop') & (Q(request_status = 'Accepted') | Q(request_status = 'Rejected')), student = student
    ).order_by('-request_responded_at')

    # Filter evaluations created by the respective student
    student_evaluations = Subject_Evaluation.objects.filter(student=student)

    # Create a paginator object with the queryset and set the number of item per page
    paginator = Paginator(classes_enrolled, 10)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the page object for the current page
    page = paginator.get_page(page_number)

    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)

    # Create a second paginator object with a different query set and set the number of item per page
    second_paginator = Paginator(added_enrolments, 20)
    second_page_number = request.GET.get('second_page')
    second_page = second_paginator.get_page(second_page_number)
    second_max_pages = second_paginator.num_pages
    second_current_page = second_page.number
    second_page_range = range(max(1, second_current_page - 2), min(second_max_pages, second_current_page + 2) + 1)

    context = {
        'classes_enrolled': page,
        'page_range': page_range,
        'added_enrolments': second_page,
        'second_page_range': second_page_range,
        'dropped_enrolments': dropped_enrolments,
        'student_evaluations': student_evaluations,
    }

    return render(request,'student_tuition_classes_list.html',context)


def student_drop_class(request,pk):

    student = get_object_or_404(Student, user=request.user)

    # Retrieve the class to be dropped
    class_dropped = get_object_or_404(Tuition_Classes, id=pk)

    # Create an enrolment request for dropping the class
    enrolment = Enrolment(
        request_type = 'Drop',
        request_status = 'Pending',
        enrolment_status = 'Active',
        tuition_classes = class_dropped,
        student = student
    )
    enrolment.save()

    messages.success(request,'Class drop request sent successfully.')

    return redirect('student_enrolment_request')

def student_add_evaluation(request,pk):

    student = get_object_or_404(Student, user=request.user)

    # Retrieve the class that user commenting
    class_evaluated = get_object_or_404(Tuition_Classes,id=pk)

    evaluation_created = Subject_Evaluation.objects.filter(student=student, tuition_classes=class_evaluated)

    context={
        'student':student,
        'class_evaluated':class_evaluated,
        'evaluation_created': evaluation_created,
    }

    if request.method == 'POST':
        evaluation_content = request.POST.get('evaluation_content')

        evaluation = Subject_Evaluation(
            subject_evaluation_content = evaluation_content,
            student = student,
            tuition_classes = class_evaluated,
        )
        evaluation.save()

        messages.success(request,'The evaluation has been successfully submitted. Thanks for your feedback!')
        return redirect('student_tuition_classes_list')
    return render (request,'student_tuition_classes_list.html',context)

def export_class_history_pdf(request, pk):
    user = request.user
    student = get_object_or_404(Student, pk=pk)
    
    added_enrolments = Enrolment.objects.filter(
        Q(request_type='Add') & (Q(request_status='Accepted') | Q(request_status='Rejected')),
        student=student
    ).order_by('-request_responded_at')

    dropped_enrolments = Enrolment.objects.filter(
        Q(request_type='Drop') & (Q(request_status='Accepted') | Q(request_status='Rejected')),
        student=student
    ).order_by('-request_responded_at')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.user.full_name}_Class Add Drop History.pdf'

    # Create a PDF document using ReportLab with landscape page layout
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))


    # Build separate tables for Add History and Drop History
    elements = []

    # PDF Header
    add_drop_pdf_header = f"<font size='15'><b><u>Class Add Drop History</u></b></font><br/><br/>"
    centered_style = getSampleStyleSheet()['Normal']
    centered_style.alignment = 1  # 1 corresponds to center alignment
    centered_header = Paragraph(add_drop_pdf_header, centered_style)
    elements.append(centered_header)

    # Add some empty lines (Spacer)
    elements.append(Spacer(1, 25))  # Adjust the height (20 in this example) as needed

    # Student details
    student_details_text = f"<font size='13'><b>Student's Full Name:</b> {student.user.full_name}<br/><br/>" \
                        f"<b>Email:</b> {student.user.email}<br/><br/>" \
                        f"<b>Education Level:</b> {student.school_level.capitalize()}<br/><br/>"

    if student.school_level == 'primary':
        if student.primary_school_type == 'sk':
            student_details_text += f"<b>Primary School Type:</b> {student.primary_school_type.capitalize()}<br/>"
            student_details_text += f"<b>SK Level:</b> {student.sk_level.capitalize()}<br/>"
        elif student.primary_school_type == 'sjkc':
            student_details_text += f"<b>Primary School Type:</b> {student.primary_school_type.capitalize()}<br/>"
            student_details_text += f"<b>SJKC Level:</b> {student.sjkc_level.capitalize()}<br/>"
    elif student.school_level == 'secondary':
        student_details_text += f"<b>SMJK Level:</b> {student.secondary_level.capitalize()}<br/>"

    # Close the <font> tag at the end
    student_details_text += "</font><br/><br/>"

    elements.append(Paragraph(student_details_text, getSampleStyleSheet()['Normal']))

    # Add some empty lines (Spacer)
    elements.append(Spacer(1, 30))  # Adjust the height (20 in this example) as needed

    # Create and format the "Add History" table
    added_history_table = create_table_from_enrollments(added_enrolments)
    added_heading = f"<font size = '12'><b>Add Class History:</b></font><br/><br/>"
    elements.append(Paragraph(added_heading, getSampleStyleSheet()['Normal']))
    elements.append(added_history_table)

    # Add some empty lines (Spacer)
    elements.append(Spacer(1, 60))  # Adjust the height (20 in this example) as needed

    # Create and format the "Drop History" table
    dropped_history_table = create_table_from_enrollments(dropped_enrolments)
    dropped_heading = f"<font size = '12'><b>Drop Class History:</b></font><br/><br/>"
    elements.append(Paragraph(dropped_heading, getSampleStyleSheet()['Normal']))
    elements.append(dropped_history_table)

    # Style the 'Add Class' table
    added_history_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#193F62')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
    ]))

    # Style the 'Add Class' table
    dropped_history_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#287051')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
    ]))
    # Build the PDF document with all elements
    doc.build(elements)

    return response

def create_table_from_enrollments(enrollments):
    # Create a list to hold the data for the table
    data = []

    # Define table column headers
    table_headers = ['Class Name', 'Subject', 'Class Time', 'Enrolment Status', 'Request Status', 'Request Responded At']

    # Add the column headers to the data list
    data.append(table_headers)

    # Iterate through enrollments and add data to the table
    for enrolment in enrollments:
        tuition_class_name = enrolment.tuition_classes.tuition_class_name
        subject = enrolment.tuition_classes.subject
        class_time = f"Every {enrolment.tuition_classes.weekly_day}\n"
        class_time += f"{enrolment.tuition_classes.general_start_time} to {enrolment.tuition_classes.general_end_time}"
        enrolment_status = enrolment.enrolment_status
        request_status = enrolment.request_status
        request_responded_at = enrolment.request_responded_at.strftime("%Y-%m-%d %H:%M:%S")
        data.append([tuition_class_name, subject, class_time, enrolment_status, request_status, request_responded_at])

    # Create the table with landscape layout
    table = Table(data, colWidths=[1.5*inch, 1.5*inch, 2.8*inch, 1.5*inch, 1.5*inch, 1.8*inch])

    return table

# Create customised timetable function

def testing(request):
    return render(request,'testing.html')


def student_timetable (request):
    user = request.user
    student = Student.objects.get(user=user)
    
    # Retrieve the currently active classes
    active_classes = get_active_classes(student)

    # Prepare the timetable data
    timetable_data = prepare_timetable_data(active_classes)
    timetable_data = sorted(timetable_data, key=lambda x: x['start_time'])

    # Define the time slots
    timetable_hours = ['08:00:00', '09:00:00', '10:00:00', '11:00:00', '12:00:00', '13:00:00', '14:00:00', '15:00:00', '16:00:00', '17:00:00', '18:00:00', '19:00:00', '20:00:00', '21:00:00','22:00:00', '23:00:00']

    context={
        'timetable_data':timetable_data,
        'timetable_hours': timetable_hours,
    }

    return render(request, 'student_timetable.html', context)

def get_active_classes(student):

    # Retrieve the 'Add' enrolments with 'Accepted' status for the student
    add_enrolments = Enrolment.objects.filter(
        request_type = 'Add',
        request_status = 'Accepted',
        student = student
    )

    # Create a list of vlass IDs for which 'Drop' requests have been accepeted
    drop_classes = set()
    for enrolment in add_enrolments:
        drop_enrolments = Enrolment.objects.filter(
            request_type = 'Drop',
            request_status = 'Accepted',
            tuition_classes = enrolment.tuition_classes
        ).first()

        if drop_enrolments:
            drop_classes.add(enrolment.tuition_classes_id)
    
    # Filter classes to display 
    active_classes = add_enrolments.exclude(tuition_classes__id__in=drop_classes)
    return active_classes

def prepare_timetable_data(active_classes):
    timetable_data = []

    for active_class in active_classes:
        # Retrieve the class details from the Tuition_Classes model
        class_details = active_class.tuition_classes

        # Extract the hour component from the general start time
        hour_component = class_details.general_start_time.strftime("%H:00:00")

        # Organize the class details into a dictionary
        class_info = {
            'class_name': class_details.tuition_class_name,
            'subject': class_details.subject,
            'weekly_day': class_details.weekly_day,  # Add the day of the week
            'time': hour_component,  # Add the time slot
            #'time': f"{class_details.general_start_time} - {class_details.general_end_time}",
            'tutor': class_details.tutor_name,
            'start_time': f"{class_details.general_start_time}",
            'end_time': f"{class_details.general_end_time}"
        }

        # Debugging: Print start times
        print(f'Start time: {class_details.general_start_time}')

        timetable_data.append(class_info)

    return timetable_data

def admin_class_dashboard(request):

    # Retrieve the total number of classes
    total_classes = Tuition_Classes.objects.count()
    subject_data = Tuition_Classes.objects.values('subject').annotate(total_classes=Count('id'))

    active_classes = Tuition_Classes.objects.filter(is_archived=False)
    archived_classes = Tuition_Classes.objects.filter(is_archived=True)

    # Extract subjects and class counts
    subjects = [entry['subject'] for entry in subject_data]
    class_counts = [entry['total_classes'] for entry in subject_data]


    # Define a mapping from full study levels to shortert labels
    study_level_labels = {
        'Kindergarten': 'K',
        'Primary sk std1': 'SK_S1',
        'Primary sk std2': 'SK_S2',
        'Primary sk std3': 'SK_S3',
        'Primary sk std4': 'SK_S4',
        'Primary sk std5': 'SK_S5',
        'Primary sk std6': 'SK_S6',
        'Primary sjkc std1': 'SJKC_S1',
        'Primary sjkc std2': 'SJKC_S2',
        'Primary sjkc std3': 'SJKC_S3',
        'Primary sjkc std4': 'SJKC_S4',
        'Primary sjkc std5': 'SJKC_S5',
        'Primary sjkc std6': 'SJKC_S6',
        'Secondary form1': 'F1',
        'Secondary form2': 'F2',
        'Secondary form3': 'F3',
        'Secondary form4': 'F4',
        'Secondary form5': 'F5',
    }
    top_classes = Tuition_Classes.objects.annotate(student_count=Count('enrolment', distinct=True, filter=Q(
        enrolment__request_type = 'Add',
        enrolment__request_status = 'Accepted'
    ))).order_by('-student_count')[:5]

    class_names = [f"{tuition_class.tuition_class_name}_{study_level_labels.get(tuition_class.tuition_class_study_level, tuition_class.tuition_class_study_level)}" for tuition_class in top_classes]
    student_counts = [tuition_class.student_count for tuition_class in top_classes]

    # Retrieve tuition classes with its respective data
    tuition_classes = Tuition_Classes.objects.all().order_by('created_at')
    #tuition_classes = Tuition_Classes.objects.filter(is_archived=False).order_by('created_at')
    active_tab = request.GET.get('active_tab')
    # Paginator
    paginator = Paginator(tuition_classes, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)

    context = {
        'total_classes': total_classes,
        'subject_data': subject_data,
        'subjects': subjects,
        'class_counts': class_counts,
        'active_classes': active_classes,
        'archived_classes': archived_classes,
        'class_names': class_names,
        'student_counts': student_counts,
        'tuition_classes': page,
        'page_range': page_range,
        'active_tab': active_tab,
    }

    return render (request, 'admin_class_dashboard.html',context)

def admin_individual_class_dashboard(request, pk):
    tuition_classes = get_object_or_404(Tuition_Classes, id=pk)

    # Retrieve the 'Add' and 'Drop' enrolments with 'Accepted' status for the specific class
    enrollments = Enrolment.objects.filter(
        tuition_classes=tuition_classes,
        request_status='Accepted',
        request_type__in=['Add', 'Drop']
    )

    # Create a dictionary to store the count of active enrollments for each class
    active_enrollments_count = {}

    # Create a dictionary to store the latest enrollment for each student
    latest_enrollment = {}

    # Iterate through enrollments to identify 'Drop' and 'Add' requests
    for enrollment in enrollments:
        student_id = enrollment.student_id
        class_id = enrollment.tuition_classes_id

        if enrollment.request_type == 'Drop':
            if student_id not in latest_enrollment or latest_enrollment[student_id]['request_type'] == 'Add':
                if class_id in active_enrollments_count:
                    active_enrollments_count[class_id] -= 1
                else:
                    active_enrollments_count[class_id] = -1

            latest_enrollment[student_id] = {
                'request_type': 'Drop',
                'class_id': class_id
            }

        if enrollment.request_type == 'Add':
            if student_id not in latest_enrollment or latest_enrollment[student_id]['request_type'] == 'Drop':
                if class_id in active_enrollments_count:
                    active_enrollments_count[class_id] += 1
                else:
                    active_enrollments_count[class_id] = 1

            latest_enrollment[student_id] = {
                'request_type': 'Add',
                'class_id': class_id
            }

    # Get the active enrollment count for the displayed class
    active_enrollments_for_class = active_enrollments_count.get(tuition_classes.id, 0)

    # Calculate the number of dropped enrollments, considering re-enrollments
    students_who_dropped_count = sum(1 for enrollment_data in latest_enrollment.values() if enrollment_data['request_type'] == 'Drop')


    # Calculate the life span of the class
    class_start_date = tuition_classes.class_start_date
    class_end_date = tuition_classes.class_end_date

    if class_start_date and class_end_date:
        class_lifespan = class_end_date - class_start_date
    else:
        class_lifespan = timedelta(days=0)

    # Retrieve the evaluations made for the respective class
    evaluations = Subject_Evaluation.objects.filter(tuition_classes=tuition_classes)

    # Create a paginator object with the queryset and set the number of item per pafe
    paginator = Paginator(evaluations, 5)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the page object for the current page
    page = paginator.get_page(page_number)

    # Calculate the range of page numbers to display
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)
    
    context = {
        'tuition_classes': tuition_classes,
        'active_enrollments_count': active_enrollments_for_class,
        'students_who_dropped_count': students_who_dropped_count,
        'class_lifespan': class_lifespan,
        'evaluations': page,
        'page_range': page_range,
    }



    return render(request, 'admin_individual_class_dashboard.html', context)

def admin_archive_student (request,pk):
    archive_student = get_object_or_404(Student, id=pk)
    active_tab = "tab2"

    archive_student.is_archived = True
    archive_student.archived_at = timezone.now()
    archive_student.unarchived_at = None
    archive_student.save()

    messages.success(request, 'The student is successfully archived.')
    return redirect(f'/admin_student_list/?active_tab={active_tab}')

def admin_unarchive_student(request,pk):
    unarchive_student = get_object_or_404(Student, id=pk)
    
    # Set the active tab to "tab1"
    active_tab = "tab1"

    if unarchive_student.is_archived:
        unarchive_student.is_archived = False
        unarchive_student.unarchived_at = timezone.now()
        unarchive_student.save()

    messages.success(request, 'The student is successfully unarchived.')
    return redirect(f'/admin_student_list/?active_tab={active_tab}')

def admin_student_dashboard(request):
    # Retrieve the total number of students
    total_students = Student.objects.count()

    active_students = Student.objects.filter(is_archived=False)
    archived_students = Student.objects.filter(is_archived=True)

    # Bar chart on students' school level
    student_school_levels_data = Student.objects.values('school_level').annotate(count=Count('id'))
    student_school_levels = [entry['school_level'] for entry in student_school_levels_data]
    student_school_levels_count = [entry['count'] for entry in student_school_levels_data]

    # Line chart on student enrollment over months
    student_enrollments = Student.objects.select_related('user').annotate(
        month=TruncMonth('user__created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    months = [entry['month'].strftime('%Y-%m') for entry in student_enrollments]
    enrollments = [entry['count'] for entry in student_enrollments]

    # Retrieve the Students
    students = Student.objects.all()
    active_tab = request.GET.get('active_tab')
    paginator = Paginator(students,10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)

    context = {
        'total_students': total_students,
        'active_students': active_students,
        'archived_students': archived_students,
        'student_school_levels': student_school_levels,
        'student_school_levels_count': student_school_levels_count,
        'months': months,
        'enrollments': enrollments,
        'students':page,
        'page_range': page_range,
        'active_tab': active_tab,
    }
    return render (request,'admin_student_dashboard.html', context)

def admin_individual_student_dashboard(request, pk):
    # Retrieve the Students
    student = get_object_or_404(Student, id=pk)

    enrollments = Enrolment.objects.filter(
        student=student,  # Filter by the specific student
        request_status='Accepted',
        request_type__in=['Add', 'Drop']
    )

    # Create a dictionary to store the count of active enrollments for each class
    active_enrollments_count = {}

    # Create a dictionary to store the latest enrollment for the specific student
    latest_enrollment = {}

    # Iterate through enrollments to identify 'Drop' and 'Add' requests
    for enrollment in enrollments:
        class_id = enrollment.tuition_classes_id

        if enrollment.request_type == 'Drop':
            if latest_enrollment.get(class_id) == 'Add':
                # Decrement the count for active enrollments for this class
                active_enrollments_count[class_id] -= 1

            latest_enrollment[class_id] = 'Drop'

        if enrollment.request_type == 'Add':
            if latest_enrollment.get(class_id) != 'Drop':
                # Increment the count for active enrollments for this class
                active_enrollments_count[class_id] = active_enrollments_count.get(class_id, 0) + 1

            latest_enrollment[class_id] = 'Add'

    # Calculate the number of active enrollments for the specific student
    active_enrollments_counts_student = sum(active_enrollments_count.values())
    # Calculate the number of dropped enrollments for the specific student
    dropped_enrollments_count_student = sum(1 for enrollment_data in latest_enrollment.values() if enrollment_data == 'Drop')
    
    created_at = student.user.created_at
    current_time = timezone.now()
    time_delta = current_time - created_at
    #Extract the number of days
    days_since_joined = time_delta.days
    
    # Filter evaluations created by the respective student
    student_evaluations = Subject_Evaluation.objects.filter(student=student)
    paginator = Paginator(student_evaluations, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    max_pages = paginator.num_pages
    current_page = page.number
    page_range = range(max(1, current_page - 2), min(max_pages, current_page + 2) + 1)
    
    context = {
        'student': student,
        'active_enrollments_counts_student': active_enrollments_counts_student,
        'dropped_enrollments_count_student' : dropped_enrollments_count_student,
        'days_since_joined': days_since_joined,
        'student_evaluations': page,
        'page_range': page_range
    }



    return render(request, 'admin_individual_student_dashboard.html', context)

def admin_payment_status(request):
    return render(request, 'admin_payment_status.html')