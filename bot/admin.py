from django.contrib import admin
from django.utils.html import format_html

from bot.models import (
    BotData,
    Certificate,
    ChatData,
    Customer,
    Impression,
    Order,
    Faq,
    SupportApplication
)


@admin.register(BotData)
class BotDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'bot_name',)
    list_display_links = ('bot_name',)


@admin.register(ChatData)
class ChatDataAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'called_at', 'data',)
    search_fields = ('chat_id',)
    readonly_fields = (
        'chat_id',
        'start_at',
        'called_at',
        'data'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Impression)
class ImpressionAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'name', 'price_in_rubles', 'for_men', 'for_girls',
        'for_couples', 'for_all'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('for_men', 'for_girls', 'for_couples', 'for_all')
    readonly_fields = ('id',)

    def has_delete_permission(self, request, obj=None):
        return False


class CertificateInline(admin.TabularInline):
    model = Certificate
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'number', 'created_at', 'recipient_name', 'receiving_method',
        'confirmed', 'given_for_delivery', 'delivered'
    )
    list_display_links = ('id', 'created_at')
    search_fields = ('id', 'number', 'recipient_name')
    list_filter = (
        'recipient_name', 'receiving_method', 'confirmed',
        'given_for_delivery', 'delivered')
    readonly_fields = (
        'id', 'created_at', 'payment_screenshot', 'get_image_preview'
    )
    raw_id_fields = ('customer', 'impression')
    inlines = (CertificateInline,)

    def get_image_preview(self, obj):
        if not obj.id or not obj.payment_screenshot:
            return ''
        return format_html(
            '<img src="{url}" style="max-height: 200px;"/>',
            url=obj.payment_screenshot.url
        )


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'tg_username', 'phone', 'fullname')
    list_display_links = ('chat_id', 'tg_username')
    search_fields = ('chat_id', 'tg_nick', 'phone', 'fullname')
    readonly_fields = ('chat_id', 'registered_at')
    inlines = (OrderInline,)


@admin.register(SupportApplication)
class SupportApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'registered_at', 'request_type', 'tg_username', 'accepted',
        'closed'
    )
    list_display_links = ('id', 'registered_at', 'request_type')
    list_filter = ('request_type', 'tg_username', 'accepted', 'closed')
    search_fields = ('request_type', 'tg_nick')
    raw_id_fields = ('order', 'certificate')


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'russian_question', 'english_question', 'availability'
    )
    list_display_links = ('number', 'russian_question', 'english_question')
    search_fields = ('number', 'russian_question', 'english_question')
    readonly_fields = ('id',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        'certificate_id', 'start_date', 'expiry_date', 'activated_at',
        'blocked', 'used'
    )
    list_display_links = ('certificate_id', 'start_date', 'expiry_date')
    search_fields = ('certificate_id', 'activated_at', 'blocked', 'used')
    raw_id_fields = ('impression', 'order')
