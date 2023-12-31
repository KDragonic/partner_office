# Generated by Django 4.2.3 on 2023-07-08 11:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('utils', '0005_mailing'),
    ]

    operations = [
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('en_name', models.CharField(max_length=255)),
                ('slug', models.CharField(blank=True, max_length=255, null=True)),
                ('coordinates', models.CharField(blank=True, max_length=255, null=True)),
                ('place_type', models.CharField(choices=[('city', 'Город'), ('town', 'Городок'), ('village', 'Деревня'), ('settlement', 'Поселок'), ('hamlet', 'Хутор'), ('suburb', 'Пригород'), ('region', 'Регион'), ('province', 'Провинция'), ('state', 'Штат'), ('country', 'Страна'), ('continent', 'Континент'), ('other', 'Другое')], max_length=255)),
                ('auto_created', models.BooleanField(default=0)),
                ('active', models.BooleanField(default=1)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='utils.place')),
            ],
        ),
        migrations.CreateModel(
            name='AdminLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
