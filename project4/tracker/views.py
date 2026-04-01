from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.db import IntegrityError

from django.shortcuts import render

# Create your views here.
@login_required
def index(request):
    return render(request, 'tracker/index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'tracker/login.html', {
                'message': 'Invalid credentials'
            })
    return render(request, 'tracker/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, 'tracker/register.html', {
                'message': 'Passwords must match'
            })
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, 'tracker/register.html', {
                'message': 'Username already taken'
            })
        login(request, user)
        return redirect('index')
    return render(request, 'tracker/register.html')
