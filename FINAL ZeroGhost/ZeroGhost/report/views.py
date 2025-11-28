from django.shortcuts import render, redirect
from .models import Report
from .forms import ReportForm
from django.contrib import messages

def index(request):
    return render(request, "report/index.html")

def submission(request):
    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save()
            messages.success(request, 'Report submitted successfully!')
            print(f"Report saved: {report.id}")  # Debug print
            return redirect("/")
        else:
            messages.error(request, 'Please fix the errors below.')
            print(f"Form errors: {form.errors}")  # Debug print
            return render(request, "report/submission.html", {'form': form})
    else:
        form = ReportForm()
    
    return render(request, "report/submission.html", {'form': form})
        
