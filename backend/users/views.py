from django.shortcuts import render, redirect
from .forms import UserLoginForm, UserRegistrationForm, UserChangePasswordForm
from django.contrib.auth import login, logout


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})


def user_logout(request):
    user = request.user
    if user.is_authenticated:
        logout(request)
    return redirect('index')


def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
        return render(request, 'users/registration.html', {'form': form})
    else:
        form = UserRegistrationForm()
    return render(request, 'users/registration.html', {'form': form})


def user_change_password(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        form = UserChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            return redirect('login')
        return render(request, 'users/change_password.html', {'form': form})
    else:
        form = UserChangePasswordForm(user=request.user)
    return render(request, 'users/change_password.html', {'form': form})


def profile(request):
    ...
