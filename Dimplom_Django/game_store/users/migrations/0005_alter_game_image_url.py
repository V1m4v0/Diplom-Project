# Generated by Django 5.1.4 on 2024-12-17 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_game_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='image_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
