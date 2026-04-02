from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.db import IntegrityError

from .models import College, Application, Task
from django.shortcuts import render
from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
@login_required
def index(request):
    applications = Application.objects.filter(user=request.user)
    
    # Calculate days until deadline for each application
    for app in applications:
        days_left = (app.college.application_deadline - date.today()).days
        app.days_until_deadline = days_left
    
    context = {
        'applications': applications
    }
    return render(request, 'tracker/index.html', context)

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

@login_required
def get_tasks(request, application_id):
    application = get_object_or_404(Application, id=application_id, user=request.user)
    tasks = application.tasks.all()
    tasks_data = [{
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'completed': task.completed,
        'due_date': task.due_date
    } for task in tasks]
    return JsonResponse({'tasks': tasks_data})

@login_required
@csrf_exempt
def toggle_task(request, task_id):
    if request.method == 'PUT':
        task = get_object_or_404(Task, id=task_id, application__user=request.user)
        task.completed = not task.completed
        task.save()
        return JsonResponse({'completed': task.completed})
    return JsonResponse({'error': 'Invalid method'}, status=400)
