from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, Listing, Bid, Comment

admin.site.site_header = "Commerce Application Admin"
admin.site.site_title = "Commerce Application Admin"
admin.site.index_title = "Commerce Application Admin"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_superuser", "is_active")


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "owner",
        "category",
        "starting_bid",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "category", "created_at", "updated_at")
    search_fields = ("title", "description", "owner__username", "category")
    autocomplete_fields = ("owner",)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "bidder", "amount", "created_at")
    search_fields = ("listing__title", "bidder__username")
    list_filter = ("created_at",)
    autocomplete_fields = ("listing", "bidder")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "author")
    search_fields = ("listing__title", "author__username", "content")
    autocomplete_fields = ("listing", "author")
