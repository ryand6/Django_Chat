# Generated by Django 4.0.7 on 2023-02-10 22:51

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0005_auto_20220424_2025'),
        ('account', '0003_accountinfo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountinfo',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
