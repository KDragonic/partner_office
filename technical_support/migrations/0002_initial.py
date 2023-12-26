# Generated by Django 4.2.3 on 2023-07-08 11:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('technical_support', '0001_initial'),
        ('hotel', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='answered',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Кто ответил'),
        ),
        migrations.AddField(
            model_name='link_u',
            name='request',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='technical_support.request'),
        ),
        migrations.AddField(
            model_name='link_u',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddField(
            model_name='link_h',
            name='hotel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hotel.hotel', verbose_name='Отель'),
        ),
        migrations.AddField(
            model_name='link_h',
            name='request',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='technical_support.request'),
        ),
    ]