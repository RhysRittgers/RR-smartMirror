from django.contrib import admin
from .models import ModuleCatalog, UserModule

@admin.register(ModuleCatalog)
class ModuleCatalogAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "version")
    search_fields = ("key", "name")

@admin.register(UserModule)
class UserModuleAdmin(admin.ModelAdmin):
    list_display = ("user", "module", "enabled", "x", "y", "w", "h", "z")
    list_filter = ("enabled", "module__key")
    search_fields = ("user__username", "module__key")
