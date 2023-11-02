from django.urls import path
from . import views

urlpatterns = [
   path('class_list_dashboard/', views.class_list_dashboard, name="class_list_dashboard"),
   path('class_requestenrolment_dashboard/', views.class_requestenrolment_dashboard, name ="class_requestenrolment_dashboard"),
   path('addsubject/', views.addsubject, name="addsubject"),
 
]