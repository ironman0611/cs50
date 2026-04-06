import re
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
from django.views.decorators.http import require_POST

from .models import Application, College, Task, UserProfile

# All College text fields used for multi-token fuzzy search (each token must match somewhere).
_COLLEGE_FUZZY_TEXT_FIELDS = (
    "name",
    "location",
    "website",
    "institution_type",
    "state",
    "campus_setting",
    "climate",
    "campus_size",
    "meal_options",
    "extracurriculars",
    "housing_summary",
    "sports_program",
    "search_notes",
)


def _college_token_q(token: str) -> Q:
    """OR across columns; partial matches (icontains), not exact preference matching."""
    combined = Q()
    for field in _COLLEGE_FUZZY_TEXT_FIELDS:
        combined |= Q(**{f"{field}__icontains": token})
    tl = token.lower()
    if tl in ("aid", "financial", "scholarship", "fafsa", "grants"):
        combined |= Q(financial_aid_available=True)
    return combined


def filter_colleges_fuzzy(queryset, raw_query: str):
    raw_query = (raw_query or "").strip()
    if not raw_query:
        return queryset
    tokens = [t for t in re.split(r"\s+", raw_query) if t]
    if not tokens:
        return queryset
    for token in tokens:
        queryset = queryset.filter(_college_token_q(token))
    return queryset


def filter_applications_by_college_fuzzy(app_queryset, raw_query: str):
    raw_query = (raw_query or "").strip()
    if not raw_query:
        return app_queryset
    tokens = [t for t in re.split(r"\s+", raw_query) if t]
    if not tokens:
        return app_queryset
    for token in tokens:
        combined = Q()
        for field in _COLLEGE_FUZZY_TEXT_FIELDS:
            combined |= Q(**{f"college__{field}__icontains": token})
        tl = token.lower()
        if tl in ("aid", "financial", "scholarship", "fafsa", "grants"):
            combined |= Q(college__financial_aid_available=True)
        app_queryset = app_queryset.filter(combined)
    return app_queryset


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
            "application_status_choices": Application.STATUS_CHOICES,
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
        colleges = filter_colleges_fuzzy(colleges, q)
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

    user_apps = Application.objects.filter(user=request.user).select_related("college")
    application_by_college_id = {app.college_id: app for app in user_apps}
    for college in page_obj:
        college.user_application = application_by_college_id.get(college.pk)

    return render(
        request,
        "tracker/all_colleges.html",
        {
            "nav_active": "all_colleges",
            "page_obj": page_obj,
            "search_query": q,
            "per_page_choice": per_page_choice,
            "application_status_choices": Application.STATUS_CHOICES,
        },
    )


@login_required
def college_detail(request, college_id):
    college = get_object_or_404(College, pk=college_id)
    user_application = (
        Application.objects.filter(user=request.user, college=college)
        .select_related("college")
        .first()
    )
    return render(
        request,
        "tracker/college_detail.html",
        {
            "nav_active": "",
            "college": college,
            "user_application": user_application,
            "application_status_choices": Application.STATUS_CHOICES,
        },
    )


@login_required
def my_colleges(request):
    q = request.GET.get("q", "").strip()
    apps = Application.objects.filter(user=request.user).select_related("college")
    if q:
        apps = filter_applications_by_college_fuzzy(apps, q)
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
            "application_status_choices": Application.STATUS_CHOICES,
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


@login_required
@require_POST
def update_application_status(request, application_id):
    application = get_object_or_404(Application, pk=application_id, user=request.user)
    new_status = request.POST.get("status", "")
    valid_statuses = {choice[0] for choice in Application.STATUS_CHOICES}
    if new_status not in valid_statuses:
        messages.error(request, "Invalid status.")
    else:
        application.status = new_status
        application.save(update_fields=["status", "updated_at"])
        messages.success(
            request,
            f'Status for "{application.college.name}" set to {application.get_status_display()}.',
        )
    next_url = request.POST.get("next", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect("my_colleges")


@login_required
@require_POST
def remove_application(request, application_id):
    application = get_object_or_404(Application, pk=application_id, user=request.user)
    college_name = application.college.name
    application.delete()
    messages.success(request, f'Removed "{college_name}" from your list.')
    next_url = request.POST.get("next", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect("my_colleges")


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


@login_required
def preferences(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.college_type_preferences = request.POST.get("college_type_preferences", "")
        profile.meal_plan_preference = request.POST.get("meal_plan_preference", "no_preference")
        profile.preferred_state = request.POST.get("preferred_state", "")
        profile.preferred_setting = request.POST.get("preferred_setting", "")
        raw_dist = request.POST.get("max_distance_from_home", "0")
        profile.max_distance_from_home = int(raw_dist) if raw_dist.isdigit() else 0
        profile.preferred_climate = request.POST.get("preferred_climate", "")
        profile.preferred_campus_size = request.POST.get("preferred_campus_size", "")
        profile.extracurriculars = ",".join(request.POST.getlist("extracurriculars"))
        profile.preferred_housing = request.POST.get("preferred_housing", "")
        profile.sports_program_preference = request.POST.get("sports_program_preference", "")
        profile.gpa_self_assessment = request.POST.get("gpa_self_assessment", "")
        raw_sat = request.POST.get("sat_act_score", "0")
        profile.sat_act_score = int(raw_sat) if raw_sat.isdigit() else 0
        profile.financial_aid_needed = request.POST.get("financial_aid_needed") == "on"
        profile.save()
        messages.success(request, "Your preferences have been saved.")
        return redirect("preferences")

    saved_extras = profile.extracurriculars.split(",") if profile.extracurriculars else []

    return render(request, "tracker/preferences.html", {
        "nav_active": "preferences",
        "profile": profile,
        "extracurricular_choices": UserProfile.EXTRACURRICULAR_CHOICES,
        "saved_extracurriculars": saved_extras,
    })
