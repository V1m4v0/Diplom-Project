from django.urls import path
from .views import register, store, login_view, cart_view, add_game, delete_game
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', register, name='register'),
    path('store/', store, name='store'),
    path('login/', login_view, name='login'),
    path('cart/', cart_view, name='cart'),
    path('login/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('add_game/', add_game, name='add_game'),
    path('delete_game/<int:game_id>/', delete_game, name='delete_game'),
]