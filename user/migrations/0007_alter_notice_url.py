# Generated by Django 4.1.3 on 2023-12-23 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_alter_notice_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='url',
            field=models.CharField(blank=True, default='/', max_length=400, null=True, verbose_name='Url'),
        ),
    ]
