# Generated by Django 4.1.3 on 2023-12-14 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0005_remove_promocode_number_of_uses_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='promocode',
            name='hotel_type',
            field=models.CharField(default='hotel', max_length=255, verbose_name='Название'),
            preserve_default=False,
        ),
    ]
