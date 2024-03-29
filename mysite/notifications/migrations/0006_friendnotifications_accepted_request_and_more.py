# Generated by Django 4.0.7 on 2023-03-21 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_friendnotifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='friendnotifications',
            name='accepted_request',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='friendnotifications',
            name='received_request',
            field=models.BooleanField(default=False),
        ),
    ]
