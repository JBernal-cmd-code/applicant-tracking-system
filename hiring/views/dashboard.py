from django.shortcuts import render


def dashboard(request):
    return render(request, "hiring/dashboard.html")
