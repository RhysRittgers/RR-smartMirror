from django.urls import path
from .views import login_view, logout_view
from .views import generate_mirror_token
from .views import mirror_authenticate
from .views import csrf_token_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('generate-token/', generate_mirror_token, name='generate_token'),
    path('mirror-auth/', mirror_authenticate, name='mirror_authenticate'),
    path('csrf/', csrf_token_view, name='get_csrf'),
]
