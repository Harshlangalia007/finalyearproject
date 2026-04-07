from django.shortcuts import render


def landing_page(request):
    return render(request, "landing.html")


def dashboard_page(request):
    return render(request, "dashboard.html")
