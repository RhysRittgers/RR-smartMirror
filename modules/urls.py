from django.urls import path
from . import views

app_name = "modules"

urlpatterns = [
    path("layout/update/", views.update_layout, name="update_layout"),
]
