# Generated by Django 2.2.7 on 2020-01-08 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('csgomatches', '0032_auto_20191211_1657'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='last_tweet',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='match',
            name='description',
            field=models.TextField(blank=True, help_text='Text is mark_safe', null=True),
        ),
    ]
