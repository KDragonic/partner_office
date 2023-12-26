# Generated by Django 4.1.3 on 2023-12-23 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_alter_bonus_rubles_options_alter_child_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notice',
            name='action',
        ),
        migrations.AddField(
            model_name='notice',
            name='url',
            field=models.URLField(blank=True, default='/', null=True, verbose_name='Url'),
        ),
        migrations.AlterField(
            model_name='notice',
            name='template',
            field=models.CharField(choices=[('registration_confirmation', 'Подтверждение регистрации'), ('contest_winner_notification', 'Уведомление о победе в конкурсе'), ('job_offer', 'Предложение о работе'), ('webinar_reminder', 'Напоминание о вебинаре'), ('daily_reminder', 'Ежедневное напоминание')], max_length=255, verbose_name='Шаблон'),
        ),
    ]