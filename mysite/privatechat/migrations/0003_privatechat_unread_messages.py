# Generated by Django 4.0.7 on 2023-03-14 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('privatechat', '0002_alter_privatechat_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='privatechat',
            name='unread_messages',
            field=models.IntegerField(default=0),
        ),
    ]