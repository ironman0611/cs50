from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .models import User, Listing, Watchlist, Bid, Comment
from datetime import datetime
from decimal import Decimal

def index(request):
    listings = Listing.objects.all()

    return render(request, "auctions/index.html" , {
        "listings": listings
    })


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
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


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
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def create_listing(request):
    if request.method == "POST":
        user = request.user
        if user.is_authenticated:
            title = request.POST["title"]
            description = request.POST["description"]
            starting_bid = request.POST["starting_bid"]
            active = True
            created_at = datetime.now()
            updated_at = datetime.now()
            image_url = request.POST["image_url"]
            category = request.POST["category"]
            listing = Listing(title=title, description=description, starting_bid=starting_bid, owner=user, is_active=active, created_at=created_at, updated_at=updated_at, image_url=image_url, category=category)
            listing.save()
            return HttpResponseRedirect(reverse("index"))
        else:
            return HttpResponseRedirect(reverse("login"))
    return render(request, "auctions/create.html")

def listing(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    top_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
    user_won = (
        request.user.is_authenticated
        and not listing.is_active
        and top_bid is not None
        and request.user == top_bid.bidder
    )
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "listing_id": listing_id,
        "top_bid": top_bid,
        "user_won": user_won,
        "winner": top_bid.bidder if top_bid else None,
    })


def watchlist(request):
    user = request.user
    if user.is_authenticated:
        if request.method == "POST":
            listing_id = request.POST.get("listing_id")
            if listing_id:
                try:
                    listing = Listing.objects.get(id=listing_id)
                except Listing.DoesNotExist:
                    return HttpResponseRedirect(reverse("index"))
                action = request.POST.get("button")
                if action == "Add to Watchlist":
                    Watchlist.objects.get_or_create(user=user, listing=listing)
                elif action == "Remove from Watchlist":
                    Watchlist.objects.filter(user=user, listing=listing).delete()
            return HttpResponseRedirect(reverse("watchlist"))
        watchlist_items = (
            Watchlist.objects.filter(user=user)
            .select_related("listing")
            .order_by("-created_at")
        )
        listings = [item.listing for item in watchlist_items]
        return render(request, "auctions/watchlist.html", {"watchlist": listings})
    else:
        return HttpResponseRedirect(reverse("login"))
        
def bid(request, listing_id):
    user = request.user
    if user.is_authenticated:
        listing = Listing.objects.get(id=listing_id)
        if request.method == "POST":
            if not listing.is_active:
                messages.error(request, "This listing is closed. No further bids are allowed.")
                return HttpResponseRedirect(reverse("listing", args=[listing_id]))

            bid_amount_str = request.POST.get("bid_amount", "0")
            try:
                bid_amount = Decimal(bid_amount_str)
            except Exception:
                messages.error(request, "Invalid bid amount.")
                return HttpResponseRedirect(reverse("listing", args=[listing_id]))

            current_top_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
            minimum_valid = listing.starting_bid if current_top_bid is None else current_top_bid.amount
            if bid_amount > minimum_valid:
                Bid.objects.create(amount=bid_amount, bidder=request.user, listing=listing)
                messages.success(request, "Your bid has been placed.")
            else:
                messages.error(request, "Your bid must be greater than the current highest bid.")
            return HttpResponseRedirect(reverse("listing", args=[listing_id]))
        else:
            return HttpResponseRedirect(reverse("login"))
    else:
        return HttpResponseRedirect(reverse("login"))
 
def close(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    if request.user != listing.owner:
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    if request.method == "POST":
        listing.is_active = False
        listing.save()
        top_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
        if top_bid is not None:
            messages.success(request, f"Listing closed. Winner: {top_bid.bidder.username} with ${top_bid.amount}.")
        else:
            messages.info(request, "Listing closed with no bids.")
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))

def delete_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    if request.user != listing.owner:
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    if request.method == "POST":
        listing.delete()
        return HttpResponseRedirect(reverse("index"))
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))

def comment(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    if request.method == "POST":
        comment = request.POST["comment"]
        Comment.objects.create(content=comment, author=request.user, listing=listing)
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))

def categories(request):
    categories = (
        Listing.objects.exclude(category="").values_list("category", flat=True).distinct()
    )
    return render(request, "auctions/categories.html", {"categories": categories})

def category(request, category):
    listings = Listing.objects.filter(category=category)
    return render(request, "auctions/category.html", {"listings": listings, "category": category})