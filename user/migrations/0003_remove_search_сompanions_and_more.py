# Generated by Django 4.1.3 on 2023-12-23 10:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_bonus_rubles_lifespan_notice'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='search',
            name='сompanions',
        ),
        migrations.AlterModelOptions(
            name='financialoperation',
            options={'verbose_name': 'Финансовая операция', 'verbose_name_plural': 'Финансовые операция'},
        ),
        migrations.RemoveField(
            model_name='child',
            name='sid',
        ),
        migrations.DeleteModel(
            name='Card',
        ),
        migrations.DeleteModel(
            name='Search',
        ),
    ]
