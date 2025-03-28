# Generated by Django 2.2.7 on 2024-07-27 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('csgomatches', '0044_remove_team_game'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='team_logo_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='team_logo_width',
            field=models.IntegerField(blank=True, help_text='i.e. 50 for 50px', null=True),
        ),
    ]
