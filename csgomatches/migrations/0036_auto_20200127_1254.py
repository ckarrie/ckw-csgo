# Generated by Django 2.2.7 on 2020-01-27 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('csgomatches', '0035_match_last_tweet_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='enable_99dmg',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='match',
            name='enable_html',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='externallink',
            name='link_type',
            field=models.CharField(choices=[('hltv_match', 'HLTV'), ('esea_match', 'ESEA Match'), ('esea_event', 'ESEA Event'), ('hltv_demo', 'Demo'), ('99dmg_match', '99DMG'), ('twitch_cast', 'Cast'), ('twitch_vod', 'VOD'), ('youtube_vod', 'VOD'), ('link', 'Link')], max_length=255),
        ),
        migrations.AlterField(
            model_name='match',
            name='hltv_match_id',
            field=models.CharField(blank=True, help_text='For HLTV Livescore during match', max_length=20, null=True),
        ),
    ]
