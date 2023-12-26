from django.contrib import admin
from .models import Request, Link_H, Link_U

# Register your models here.

class U_LModelInline(admin.TabularInline):
    model = Link_U

class H_LModelInline(admin.TabularInline):
    model = Link_H

class RequestAdmin(admin.ModelAdmin):
    list_display = ("rid", "text", "title", "date", "status", "answered")

    inlines = [U_LModelInline, H_LModelInline]

admin.site.register(Request, RequestAdmin)