from django.shortcuts import render

def email_dashboard(request):
    # Email AI dashboard
    return render(request, 'email_ai/dashboard.html')
