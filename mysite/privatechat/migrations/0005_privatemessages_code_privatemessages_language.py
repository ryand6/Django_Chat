# Generated by Django 4.0.7 on 2023-06-03 23:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('privatechat', '0004_alter_privatemessages_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='privatemessages',
            name='code',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='privatemessages',
            name='language',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
