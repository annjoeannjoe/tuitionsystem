from django.shortcuts import render

# Create your views here.
def class_requestenrolment_dashboard(request):
    return render (request, "class_requestenrolment_dashboard.html")

def addsubject(request):
    return render (request,"addsubject.html")

def class_list_dashboard (request):
    return render (request, "class_list_dashboard.html")