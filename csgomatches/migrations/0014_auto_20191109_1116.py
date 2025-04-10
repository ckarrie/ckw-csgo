# Generated by Django 2.2.7 on 2019-11-09 10:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('csgomatches', '0013_auto_20191109_1103'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link_type', models.CharField(choices=[('hltv_match', 'HLTV Matchlink'), ('99dmg_match', '99DMG Matchlink'), ('twitch_cast', 'Twitch Cast'), ('twitch_vod', 'Twitch VOD'), ('youtube_vod', 'Youtube VOD')], max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('url', models.URLField()),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='csgomatches.Match')),
            ],
        ),
        migrations.DeleteModel(
            name='Cast',
        ),
    ]
