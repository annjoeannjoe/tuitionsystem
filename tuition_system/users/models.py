from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Users require an email field')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User (AbstractUser):
    objects = UserManager()
    email = models.EmailField('email address', unique=True)
    USERNAME_FIELD = 'email' #the email field of the User model will be used as the unique identifier for the user -> will be prompted to enter email address as the username
    REQUIRED_FIELDS = [] #indicate a list of fields that must be supplied when creating a user using the createsuperuser command > this to actually indicate no additional fields required when creating a superuser
    username = None
    first_name = None
    last_name = None
    full_name = models.CharField(max_length=50)
    password = models.CharField(max_length=128)
    street1 = models.CharField(max_length=50, null=True)
    street2 = models.CharField(max_length=50, null=True)
    city = models.CharField(max_length=50, null=True)
    postalcode = models.CharField(max_length=5, null=True)
    state = models.CharField(max_length=20,null=True)
    phone_code = models.CharField(max_length=5, null=True)
    phone_no = models.CharField(max_length=20, null=True)
    ROLES = (
        ('SUPER ADMIN', 'SUPER ADMIN'),
        ('ADMIN', 'ADMIN'),
        ('STUDENT', 'STUDENT'),
    )
    role = models.CharField(max_length=20, choices=ROLES, null=True)
    created_at = models.DateTimeField(auto_now_add=True) # will automatically set the value of this field to the current date and time when the user is created
    last_login = models.DateTimeField(auto_now=True)
   #haven't put is_archived and archived_at
    #reset_token = models.CharField(max_length=255, null=True, blank=True)
    #reset_token_expiration = models.DateTimeField(null=True, blank=True)

    #def is_reset_token_valid(self):
        #if self.reset_token and self.reset_token_expiration:
          #  return not (self.reset_token_expiration < timezone.now())
        #return False
    
class Student (models.Model):
    #indicate foreign key
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    SCHOOL_LEVEL = (
        ('Kindergarten', 'Kindergarten'),
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
    )
    school_level = models.CharField(max_length=20, choices=SCHOOL_LEVEL, null=True)
    PRIMARY_SCHOOL_TYPE = (
        ('SK', 'SK'),
        ('SJKC', 'SJKC'),
    )
    primary_school_type = models.CharField(max_length=20, choices=PRIMARY_SCHOOL_TYPE, null=True)
    SK_LEVEL = (
        ('Standard 1', 'Standard 1'),
        ('Standard 2', 'Standard 2'),
        ('Standard 3', 'Standard 3'),
        ('Standard 4', 'Standard 4'),
        ('Standard 5', 'Standard 5'),
        ('Standard 6', 'Standard 6'),
    )
    sk_level = models.CharField(max_length=20, choices=SK_LEVEL, null=True)
    SJKC_LEVEL = (
        ('Standard 1', 'Standard 1'),
        ('Standard 2', 'Standard 2'),
        ('Standard 3', 'Standrad 3'),
        ('Standard 4', 'Standard 4'),
        ('Standard 5', 'Standard 5'),
        ('Standard 6', 'Standard 6'),
    )
    sjkc_level = models.CharField(max_length=20,choices=SJKC_LEVEL, null=True)
    SECONDARY_LEVEL = (
        ('Form 1', 'Form 1'),
        ('Form 2', 'Form 2'),
        ('Form 3', 'Form 3'),
        ('Form 4', 'Form 4'),
        ('Form 5', 'Form 5'),
        ('Form 6', 'Form 6'),
    )
    secondary_level = models.CharField(max_length=20, choices=SECONDARY_LEVEL, null=True)
    startdate = models.DateTimeField(auto_now_add=True)
    classin_phonecode = models.CharField(max_length=10,null=True)
    classin_phoneno = models.CharField(max_length=20, null=True)
    parent_phoneno2 = models.CharField(max_length=20, null=True)
    bankin_receipt = models.FileField(upload_to='bankin_receipt/')
    student_phoneno = models.CharField(max_length=20, null=True, blank=True) # null=True: used for database-level consideration | blank=True: used for form-level consideration in which the field allowed to be empty when submitting data through a form
    student_ic_number = models.CharField(max_length=20, null=True)
    student_ic_photo = models.FileField(upload_to='student_ic_photo/')
    student_photo = models.FileField(upload_to='student_photo/')
    school_name = models.CharField(max_length=50)
    KNOW_US_FROM = (
        ('Facebook', 'Facebook'),
        ('Instagram', 'Instagram'),
        ('Google', 'Google'),
        ('Tik Tok', 'Tik Tok'),
        ('Friend', 'Friend'),
        ('小红书', '小红书'),
        ('Sibling','Sibling')
    )
    know_us_from = models.CharField(max_length=50, null=True)
    terms_and_conditions = models.BooleanField(default=False) # default is set to False as they havent agreed by default
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    unarchived_at = models.DateTimeField(null=True, blank=True)

class Admin (models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Announcement (models.Model):
    TARGETED_GROUPS = (
        ('','Select targeted group'),
        ('ALL', 'All Users'),
        ('ADMIN', 'Administrators'),
        ('STUDENT', 'Students'),
    )
    targeted_group = models.CharField(max_length=20, choices=TARGETED_GROUPS, null=True)
    announcement_title = models.CharField(max_length=255, null=True)
    announcement_content = models.TextField()
    announcement_posted_by = models.ForeignKey(Admin, on_delete=models.CASCADE) # using admin_id
    announcement_posted_at = models.DateTimeField(auto_now_add=True)
 
class Tuition_Classes(models.Model):
    tuition_class_name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    tuition_class_study_level = models.CharField(max_length=50)
    general_start_time = models.TimeField()
    general_end_time = models.TimeField()
    WEEKDAYS = (
        ('Monday','Monday'),
        ('Tuesday','Tuesday'),
        ('Wednesday','Wednesday'),
        ('Thursday','Thursday'),
        ('Friday','Friday'),
        ('Saturday','Saturday'),
        ('Sunday','Sunday')
    )
    weekly_day = models.CharField(max_length=10, choices=WEEKDAYS)
    tutor_name = models.CharField(max_length=100)
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, default=None)
    class_start_date = models.DateField(null=True, blank=True)
    class_end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    unarchived_at = models.DateTimeField(null=True, blank=True)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)

class Enrolment (models.Model):
    REQUEST_CHOICES =(
        ('Add', 'Add Class'),
        ('Drop', 'Drop Class'),
    )

    request_type = models.CharField(max_length=4, choices=REQUEST_CHOICES,null=True, blank=True)
    request_status = models.CharField(max_length=50) # To indicate whether the enrolment request has been approved or rejected or pending
    request_created_at = models.DateTimeField(auto_now_add=True)
    request_responded_at = models.DateTimeField(null=True, blank=True)
    enrolment_status = models.CharField(max_length=50) # Active or Stop
    enrol_at = models.DateTimeField(null=True, blank=True)
    is_stop = models.BooleanField(default=False)
    stop_at = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(blank=True)
    accumulated_enrol_days = models.PositiveIntegerField(default=0)
    tuition_classes = models.ForeignKey(Tuition_Classes, on_delete = models.CASCADE)
    student = models.ForeignKey(Student, on_delete = models.CASCADE)

    def calculate_accumulated_enrol_days(self):
        if self.enrol_at:
            today = timezone.now().date()
            enrolment_date = self.enrol_at.date()
            self.accumulated_enrol_days = (today - enrolment_date).days
        else:
            self.accumulated_enrol_days = 0

class Calendar_Events(models.Model):
    EVENT_TYPES = (
        ('holiday', 'Holiday'),
        ('meeting', 'Meeting'),
        ('event', 'Event'),
    )

    event_name = models.CharField(max_length=100) 
    event_description = models.CharField(max_length=100)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now_add=True)

class Subject_Evaluation(models.Model):
    subject_evaluation_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    student = models.ForeignKey(Student, on_delete = models.CASCADE)
    tuition_classes = models.ForeignKey(Tuition_Classes, on_delete = models.CASCADE)
    
