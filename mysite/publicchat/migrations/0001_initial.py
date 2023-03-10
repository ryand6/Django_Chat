# Generated by Django 4.0.7 on 2023-02-05 13:44

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, unique=True, validators=[django.core.validators.MinLengthValidator(3, 'Title must be greater than 2 characters')])),
                ('users', models.ManyToManyField(blank=True, help_text='Users currently in the chat', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PublicMessages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='publicchat.publicchat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
