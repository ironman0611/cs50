from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Post, User


def paginate_posts(request, posts_queryset):
    paginator = Paginator(posts_queryset, 10)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def index(request):
    posts = paginate_posts(request, Post.objects.order_by("-timestamp").all())
    return render(
        request,
        "network/index.html",
        {"posts": posts, "page_heading": "All Posts"},
    )


@login_required
def following_view(request):
    following_ids = request.user.following.values_list("pk", flat=True)
    posts = paginate_posts(
        request,
        Post.objects.filter(user_id__in=following_ids)
        .select_related("user")
        .order_by("-timestamp"),
    )
    return render(
        request,
        "network/index.html",
        {"posts": posts, "page_heading": "Following"},
    )


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = paginate_posts(
        request, Post.objects.filter(user=profile_user).order_by("-timestamp")
    )
    follower_count = profile_user.followers.count()
    following_count = profile_user.following.count()
    show_follow_button = (
        request.user.is_authenticated and request.user != profile_user
    )
    is_following = (
        request.user.is_authenticated
        and show_follow_button
        and request.user.following.filter(pk=profile_user.pk).exists()
    )
    return render(
        request,
        "network/profile.html",
        {
            "profile_user": profile_user,
            "posts": posts,
            "follower_count": follower_count,
            "following_count": following_count,
            "show_follow_button": show_follow_button,
            "is_following": is_following,
        },
    )


@login_required
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return HttpResponseRedirect(reverse("profile", args=[username]))
    if request.method == "POST":
        if request.user.following.filter(pk=target.pk).exists():
            request.user.following.remove(target)
        else:
            request.user.following.add(target)
    return HttpResponseRedirect(reverse("profile", args=[username]))


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

@login_required
def post(request):
    if request.method == "POST":
        content = request.POST["content"]
        Post.objects.create(content=content, user=request.user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/post.html")