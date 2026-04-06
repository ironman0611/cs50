from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import BooleanField, Case, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Application, College, Task


@login_required
def index(request):
    today = date.today()
    soon = today + timedelta(days=30)
    apps = Application.objects.filter(user=request.user).select_related("college")

    metric_total = apps.count()
    metric_pending = apps.filter(status__in=["researching", "applying"]).count()
    metric_submitted = apps.filter(status="submitted").count()
    metric_deferred = apps.filter(status="deferred").count()
    metric_accepted = apps.filter(status="accepted").count()
    metric_rejected = apps.filter(status="rejected").count()
    metric_deadline_soon = apps.filter(
        college__application_deadline__gte=today,
        college__application_deadline__lte=soon,
    ).count()
    metric_overdue = (
        apps.filter(college__application_deadline__lt=today)
        .exclude(status__in=["accepted", "rejected", "submitted"])
        .count()
    )

    upcoming = list(apps)
    for app in upcoming:
        app.days_until_deadline = (app.college.application_deadline - today).days
    upcoming.sort(key=lambda a: a.college.application_deadline)
    upcoming = upcoming[:12]

    return render(
        request,
        "tracker/index.html",
        {
            "nav_active": "dashboard",
            "applications": upcoming,
            "metric_total": metric_total,
            "metric_pending": metric_pending,
            "metric_submitted": metric_submitted,
            "metric_deferred": metric_deferred,
            "metric_accepted": metric_accepted,
            "metric_rejected": metric_rejected,
            "metric_deadline_soon": metric_deadline_soon,
            "metric_overdue": metric_overdue,
        },
    )


@login_required
def all_colleges(request):
    q = request.GET.get("q", "").strip()
    per_page_raw = request.GET.get("per_page", "20").lower()
    if per_page_raw == "all":
        per_page_choice = "all"
    elif per_page_raw == "10":
        per_page_choice = "10"
    else:
        per_page_choice = "20"

    week_ago = timezone.now() - timedelta(days=7)
    colleges = College.objects.all()
    if q:
        colleges = colleges.filter(
            Q(name__icontains=q) | Q(location__icontains=q)
        )
    colleges = colleges.annotate(
        recent_order=Case(
            When(created_at__gte=week_ago, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ),
        is_new_this_week=Case(
            When(created_at__gte=week_ago, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
    ).order_by("recent_order", "-created_at", "name")

    total_count = colleges.count()
    if per_page_choice == "all":
        per_page = max(total_count, 1)
    else:
        per_page = int(per_page_choice)

    paginator = Paginator(colleges, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    applied_ids = set(
        Application.objects.filter(user=request.user).values_list(
            "college_id", flat=True
        )
    )
    return render(
        request,
        "tracker/all_colleges.html",
        {
            "nav_active": "all_colleges",
            "page_obj": page_obj,
            "search_query": q,
            "per_page_choice": per_page_choice,
            "applied_college_ids": applied_ids,
        },
    )


@login_required
def my_colleges(request):
    q = request.GET.get("q", "").strip()
    apps = Application.objects.filter(user=request.user).select_related("college")
    if q:
        apps = apps.filter(
            Q(college__name__icontains=q) | Q(college__location__icontains=q)
        )
    apps = apps.order_by("college__application_deadline")
    today = date.today()
    for app in apps:
        app.days_until_deadline = (app.college.application_deadline - today).days
    return render(
        request,
        "tracker/my_colleges.html",
        {
            "nav_active": "my_colleges",
            "applications": apps,
            "search_query": q,
        },
    )


@login_required
def apply_college(request):
    if request.method != "POST":
        return redirect("all_colleges")
    college_id = request.POST.get("college_id")
    if not college_id:
        messages.error(request, "No college selected.")
        return redirect("all_colleges")
    college = get_object_or_404(College, pk=college_id)
    next_url = request.POST.get("next", "")
    _, created = Application.objects.get_or_create(
        user=request.user,
        college=college,
        defaults={"status": "researching"},
    )
    if created:
        messages.success(request, f'Added "{college.name}" to your list.')
    else:
        messages.info(request, f'"{college.name}" is already on your list.')
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect("all_colleges")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        return render(
            request,
            "tracker/login.html",
            {"message": "Invalid credentials"},
        )
    return render(request, "tracker/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(
                request,
                "tracker/register.html",
                {"message": "Passwords must match"},
            )
        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:
            return render(
                request,
                "tracker/register.html",
                {"message": "Username already taken"},
            )
        login(request, user)
        return redirect("index")
    return render(request, "tracker/register.html")


@login_required
def get_tasks(request, application_id):
    application = get_object_or_404(Application, id=application_id, user=request.user)
    tasks = application.tasks.all()
    tasks_data = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "due_date": str(task.due_date) if task.due_date else None,
        }
        for task in tasks
    ]
    return JsonResponse({"tasks": tasks_data})


@login_required
@csrf_exempt
def toggle_task(request, task_id):
    if request.method == "PUT":
        task = get_object_or_404(Task, id=task_id, application__user=request.user)
        task.completed = not task.completed
        task.save()
        return JsonResponse({"completed": task.completed})
    return JsonResponse({"error": "Invalid method"}, status=400)
