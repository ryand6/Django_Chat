# Generated by Django 4.0.7 on 2023-03-16 19:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifications',
            name='recipient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_recipient', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='notifications',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_sender', to=settings.AUTH_USER_MODEL),
        ),
    ]
