# Generated by Django 4.1.3 on 2023-12-23 11:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_remove_search_сompanions_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bonus_rubles',
            options={'verbose_name': 'Бонус пользователя', 'verbose_name_plural': 'Бонусы пользователя'},
        ),
        migrations.AlterModelOptions(
            name='child',
            options={'verbose_name': 'Ребёнок', 'verbose_name_plural': 'Дети'},
        ),
        migrations.AlterModelOptions(
            name='companion',
            options={'verbose_name': 'Компаньен', 'verbose_name_plural': 'Компаньены'},
        ),
        migrations.AlterModelOptions(
            name='notice',
            options={'verbose_name': 'Уведомление+', 'verbose_name_plural': 'Уведомления+'},
        ),
        migrations.RemoveField(
            model_name='notice',
            name='deleted_at',
        ),
        migrations.RemoveField(
            model_name='notice',
            name='param',
        ),
        migrations.RemoveField(
            model_name='notice',
            name='url',
        ),
        migrations.AddField(
            model_name='notice',
            name='action',
            field=models.JSONField(blank=True, default=dict, verbose_name='Действиe'),
        ),
        migrations.AddField(
            model_name='notice',
            name='option',
            field=models.JSONField(blank=True, default=dict, verbose_name='Опции'),
        ),
        migrations.AlterField(
            model_name='notice',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата создания'),
        ),
        migrations.AlterField(
            model_name='notice',
            name='push',
            field=models.CharField(choices=[('not_shown', 'Не показывать'), ('not_viewed', 'Ещё не показано'), ('shown', 'Показано')], default='not_viewed', max_length=20, verbose_name='Push'),
        ),
        migrations.AlterField(
            model_name='notice',
            name='template',
            field=models.CharField(max_length=255, verbose_name='Шаблон'),
        ),
        migrations.AlterField(
            model_name='notice',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='notice',
            name='view_type',
            field=models.CharField(choices=[('not_viewed', 'Ещё не показано'), ('shown', 'Показано'), ('visited', 'Перешёл')], default='not_viewed', max_length=20, verbose_name='Тип просмотра'),
        ),
        migrations.AlterField(
            model_name='notice',
            name='viewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата просмотра'),
        ),
    ]
