from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('service_list')
    else:
        form = UserCreationForm()
    return render(request, 'appointments/signup.html', {'form': form})


@login_required
def login_redirect_view(request):
    if request.user.is_staff:
        return redirect('owner_dashboard')
    return redirect('service_list')
