from django.contrib.auth.models import User
from django.db import models

class Game(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='game_images/', null=True, blank=True)

    def __str__(self):
        return self.title

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    games = models.ManyToManyField(Game)

    def __str__(self):
        return f"Cart of {self.user.username}"