# Generated by Django 4.0.7 on 2023-03-22 21:18

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0007_friendnotifications_friend_request_id'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='friendnotifications',
            unique_together={('sender', 'recipient', 'friend_request_id')},
        ),
    ]