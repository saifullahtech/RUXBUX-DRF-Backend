from django.contrib import admin
from django.utils.html import format_html

from .models import Address, CustomerReview, Order, ReviewAttachment


admin.site.site_header = "RUXBUX Admin"
admin.site.site_title = "RUXBUX Admin"
admin.site.index_title = "Store Management"


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Saved Address Key", {"fields": ("session_key",)}),
        ("Customer", {"fields": ("full_name", "phone")}),
        ("Address", {"fields": ("address", "city")}),
        ("Meta", {"fields": ("created_at",)}),
    )


class ReviewAttachmentInline(admin.TabularInline):
    model = ReviewAttachment
    extra = 1
    readonly_fields = ("image_preview", "created_at")
    fields = ("image", "image_preview", "alt_text", "created_at")

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not obj.pk or not obj.image:
            return "-"

        return format_html(
            '<img src="{}" style="width:80px;height:80px;object-fit:cover;border-radius:6px;" />',
            obj.image.url,
        )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [AddressInline]

    list_display = (
        "id",
        "status_badge",
        "status",
        "quantity",
        "total_amount",
        "shipping_amount",
        "discount_amount",
        "tax_amount",
        "email",
        "session_key_short",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "status_badge")
    list_editable = ("status",)
    ordering = ("-created_at",)

    list_filter = (
        "status",
        "quantity",
        ("created_at", admin.DateFieldListFilter),
        ("updated_at", admin.DateFieldListFilter),
    )

    search_fields = (
        "id",
        "public_id",
        "email",
        "session_key",
        "address__phone",
        "address__full_name",
        "address__city",
        "address__address",
    )

    date_hierarchy = "created_at"
    readonly_fields = ("id", "public_id", "created_at", "updated_at")
    list_per_page = 50
    show_full_result_count = False

    fieldsets = (
        ("Order Identity", {"fields": ("id", "public_id", "status", "session_key", "email")}),
        ("Order Quantities", {"fields": ("quantity",)}),
        (
            "Pricing Breakdown (PKR)",
            {
                "fields": (
                    "subtotal_amount",
                    "shipping_amount",
                    "tax_amount",
                    "discount_amount",
                    "total_amount",
                )
            },
        ),
        ("Customer Note", {"fields": ("customer_note",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        color_map = {
            Order.STATUS_PENDING: "#f0ad4e",
            Order.STATUS_CONFIRMED: "#0275d8",
            Order.STATUS_SHIPPED: "#5bc0de",
            Order.STATUS_DELIVERED: "#5cb85c",
            Order.STATUS_CANCELED: "#d9534f",
        }
        color = color_map.get(obj.status, "#777")
        return format_html(
            '<span style="padding:4px 10px;border-radius:999px;background:{};color:#fff;font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Session", ordering="session_key")
    def session_key_short(self, obj):
        return (obj.session_key[:10] + "...") if obj.session_key else "-"


@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    inlines = [ReviewAttachmentInline]

    list_display = (
        "id",
        "stars",
        "name",
        "email",
        "attachment_count",
        "created_at",
    )
    list_display_links = ("id", "name")
    ordering = ("-created_at",)
    list_filter = (
        "stars",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "name",
        "email",
        "text",
        "attachments__alt_text",
    )
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50
    show_full_result_count = False

    fieldsets = (
        ("Rating", {"fields": ("stars",)}),
        ("Customer", {"fields": ("name", "email")}),
        ("Review", {"fields": ("text",)}),
        ("Meta", {"fields": ("created_at",)}),
    )

    @admin.display(description="Images")
    def attachment_count(self, obj):
        return obj.attachments.count()


@admin.register(ReviewAttachment)
class ReviewAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "review",
        "image_preview",
        "alt_text",
        "created_at",
    )
    list_display_links = ("id", "image_preview")
    ordering = ("-created_at",)
    list_filter = (("created_at", admin.DateFieldListFilter),)
    search_fields = (
        "review__name",
        "review__email",
        "review__text",
        "alt_text",
    )
    readonly_fields = ("image_preview", "created_at")
    fields = ("review", "image", "image_preview", "alt_text", "created_at")

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not obj.pk or not obj.image:
            return "-"

        return format_html(
            '<img src="{}" style="width:80px;height:80px;object-fit:cover;border-radius:6px;" />',
            obj.image.url,
        )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "full_name",
        "phone",
        "city",
        "session_key_short",
        "created_at",
    )
    ordering = ("-created_at",)
    list_filter = (
        "city",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "order__id",
        "order__public_id",
        "session_key",
        "full_name",
        "phone",
        "city",
        "address",
    )
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Linking", {"fields": ("order", "session_key")}),
        ("Customer", {"fields": ("full_name", "phone")}),
        ("Address", {"fields": ("address", "city")}),
        ("Meta", {"fields": ("created_at",)}),
    )

    @admin.display(description="Session", ordering="session_key")
    def session_key_short(self, obj):
        return (obj.session_key[:10] + "...") if obj.session_key else "-"
