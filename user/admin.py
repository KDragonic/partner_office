from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.apps import apps
from django.db.models import QuerySet, Q
from .models import *
from django_json_widget.widgets import JSONEditorWidget

class MyUserAdmin(admin.ModelAdmin):
    list_display = ("id", "uid", "email", "username", "lastname", "middlename", "user_type", "is_admin", "is_superuser", "token_telegram", "token_google", "token_vk")
    search_fields = ("uid", "email")
    readonly_fields = ("uid", "id", "date_joined", "last_login", 'password')
    filter_horizontal = ()
    list_filter = ()
    list_per_page = 1000

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def get_queryset(self, request):
        qs : QuerySet = super().get_queryset(request)
        return qs.filter(~Q(additional_info__has_key="main_account"))

    def has_add_permission(self, request):
        return False

admin.site.register(User, MyUserAdmin)

class Bonus_rublesAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "value", "date")
    search_fields = ("user",)


admin.site.register(Bonus_rubles, Bonus_rublesAdmin)

class FinancialOperationAdmin(admin.ModelAdmin):
    list_display = ("user", "price", "datetime", "operation_type", "comments")
    search_fields = ("user", "datetime", "operation_type")


admin.site.register(FinancialOperation, FinancialOperationAdmin)


class NoticeAdmin(admin.ModelAdmin):
    list_display = ('user', 'template', 'message', 'push', 'view_type', 'created_at', 'viewed_at')
    search_fields = ('user__username', 'template')
    list_filter = ('push', 'view_type')
    readonly_fields = ('push', 'view_type', 'created_at', 'viewed_at')

    actions = ['update_hash']

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def message(self, obj : Notice):
        return format_html(obj.get_template("website", reset=True))

    message.short_description = 'Действие'
    message.admin_order_field = 'action'

    def update_hash(self, request, queryset : QuerySet[Notice]):
        for notice in queryset:
            for template_type in ['telegram', 'email', 'website']:
                notice.get_template(template_type)

    update_hash.short_description = "Обновить хеш шаблонов"

admin.site.register(Notice, NoticeAdmin)


# app_models = apps.get_models()
# for model in app_models:
#     if not admin.site.is_registered(model):
#         class ModelAdmin(admin.ModelAdmin):
#             list_display = [field.name for field in model._meta.fields]
#         admin.site.register(model, ModelAdmin)
