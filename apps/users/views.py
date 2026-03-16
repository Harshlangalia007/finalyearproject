from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log the user in after registration
            login(request, user)
            return redirect("/")  # Redirect to homepage
    else:
        form = UserCreationForm()

    return render(request, "users/register.html", {"form": form})
