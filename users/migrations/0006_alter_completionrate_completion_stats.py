# Generated by Django 5.1.5 on 2025-02-01 03:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_completionrate_completion_stats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='completionrate',
            name='completion_stats',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='completion_stats', to='users.completionstats'),
        ),
    ]
