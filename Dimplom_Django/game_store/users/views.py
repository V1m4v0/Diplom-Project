from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login
from .models import Game, Cart

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует.')
        elif password != confirm_password:
            messages.error(request, 'Пароли не совпадают.')
        else:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            login(request, user)
            return redirect('store')
    return render(request, 'register.html')


def store(request):
    games = Game.objects.all()
    user = request.user if request.user.is_authenticated else None

    if request.method == 'POST':
        if request.user.is_authenticated:
            game_id = request.POST.get('game_id')
            game = Game.objects.get(id=game_id)

            cart, created = Cart.objects.get_or_create(user=request.user)
            cart.games.add(game)
            messages.success(request, f'Игра {game.title} добавлена в корзину.')
        else:
            messages.error(request, 'Вы должны войти в систему, чтобы добавить игры в корзину.')

    return render(request, 'store.html', {'games': games, 'user': user})

from django.contrib.auth import authenticate, login as auth_login

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('store')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    return render(request, 'login.html')


def cart_view(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        games = cart.games.all()

        if request.method == 'POST':
            game_id = request.POST.get('game_id')
            game = Game.objects.get(id=game_id)
            cart.games.remove(game)
            messages.success(request, f'Игра {game.title} удалена из корзины.')

        return render(request, 'cart.html', {'games': games})
    else:
        messages.error(request, 'Вы должны войти в систему, чтобы просмотреть корзину.')
        return redirect('login')

from django.shortcuts import render, redirect, get_object_or_404
from .forms import GameForm

def add_game(request):
    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Игра успешно добавлена!')
            return redirect('store')
    else:
        form = GameForm()
    return render(request, 'add_game.html', {'form': form})

from .models import Game
from django.contrib import messages

def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if request.user.is_superuser:  # Проверка на администратора
        game.delete()
        messages.success(request, f'Игра {game.title} успешно удалена!')
    else:
        messages.error(request, 'У вас нет прав для удаления этой игры.')
    return redirect('store')