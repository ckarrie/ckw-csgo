# Generated by Django 2.2.7 on 2024-07-27 10:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('csgomatches', '0041_auto_20200205_1050'),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='i.e. "TrackMania" or "Counter-Strike"', max_length=255)),
                ('name_short', models.CharField(help_text='i.e. "tm", "cs"', max_length=4)),
                ('slug', models.SlugField()),
            ],
        ),
        migrations.AddField(
            model_name='csgositesetting',
            name='site_teams',
            field=models.ManyToManyField(null=True, to='csgomatches.Team'),
        ),
        migrations.AlterField(
            model_name='externallink',
            name='link_type',
            field=models.CharField(choices=[('hltv_match', 'HLTV'), ('esea_match', 'ESEA Match'), ('esea_event', 'ESEA Event'), ('hltv_demo', 'Demo'), ('99dmg_match', '99DMG'), ('twitch_cast', 'Cast'), ('twitch_vod', 'Twitch VOD'), ('youtube_vod', 'YouTube VOD'), ('link', 'Link')], max_length=255),
        ),
        migrations.AddField(
            model_name='team',
            name='game',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='csgomatches.Game'),
        ),
    ]
