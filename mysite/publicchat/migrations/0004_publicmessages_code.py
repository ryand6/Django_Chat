# Generated by Django 4.0.7 on 2023-06-03 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publicchat', '0003_remove_privatemessages_room_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicmessages',
            name='code',
            field=models.BooleanField(default=False),
        ),
    ]
