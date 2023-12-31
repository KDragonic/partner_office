# Generated by Django 4.1.3 on 2023-12-22 14:02

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0009_alter_shortlink_option_alter_shortlink_short_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentationPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('content', tinymce.models.HTMLField()),
                ('order', models.IntegerField(default=0)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='utils.documentationpage')),
                ('related_pages', models.ManyToManyField(blank=True, related_name='related', to='utils.documentationpage')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
