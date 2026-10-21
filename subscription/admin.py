from django.contrib import admin

from subscription.models import Package, PackagePlan, Subscription


admin.site.register(Package)
admin.site.register(PackagePlan)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "package", "active", "start_date", "expiry_date")
    list_display_links = ("subscriber",)
    list_filter = ("active", "package")
    search_fields = (
        "user__email",
        "user__username",
        "user__first_name",
        "user__last_name",
        "package__title",
    )
    list_select_related = ("user", "package")
    date_hierarchy = "start_date"
    ordering = ("-start_date",)
    list_per_page = 50

    @admin.display(description="Subscriber", ordering="user__email")
    def subscriber(self, obj):
        user = obj.user
        full_name = user.get_full_name().strip()
        email = getattr(user, "email", "")

        if full_name and email:
            return f"{full_name} ({email})"
        return full_name or email or user.get_username()
