from django.urls import path
from . import views

app_name = "Dashboard"

urlpatterns = [
    # Remote home (your existing page)
    path("", views.mobile_dashboard, name="mobile_dashboard"),

    # Module Store + APIs
    path("store/", views.app_store, name="app_store"),
    path("modules/<int:module_id>/toggle/", views.toggle_module, name="toggle_module"),
    path("user-modules/<int:user_module_id>/settings/", views.save_module_settings, name="save_module_settings"),
]
