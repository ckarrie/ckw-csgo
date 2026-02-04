from django.urls import reverse
from rest_framework import serializers
from django.apps import apps
from django.utils import timezone

from . import ser_objects

class CSGOTournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.Tournament')
        fields = [
            'id', 'name', 'name_alt', 
            #'name_hltv', 'name_99dmg'
        ]


class CSGOTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.Team')
        fields = [
            'id', 'name', 'name_long', 'name_alt', 
            'hltv_id',
        ]


class CSGOPlayerShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.Player')
        fields = ['ingame_name',]


class CSGOPlayerRoleShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.PlayerRole')
        fields = ['name',]

class CSGOLineupPlayerSerializer(serializers.ModelSerializer):
    player = CSGOPlayerShortSerializer()
    role = CSGOPlayerRoleShortSerializer()

    class Meta:
        model = apps.get_model('csgomatches.LineupPlayer')
        fields = ['player', 'role', ]


class CSGOLineupSerializer(serializers.ModelSerializer):
    team = CSGOTeamSerializer(read_only=True)
    players = CSGOLineupPlayerSerializer(many=True, read_only=True, source='lineupplayer_set')

    class Meta:
        model = apps.get_model('csgomatches.Lineup')
        fields = ['id', 'team', 'team_logo_url', 'active_from', 'players']

class CSGOMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.Map')
        fields = ['id', 'name', 'cs_name']

class CSGOMatchMapSerializer(serializers.ModelSerializer):
    map_pick_of = CSGOLineupSerializer(read_only=True)
    played_map = CSGOMapSerializer(read_only=True)

    class Meta:
        model = apps.get_model('csgomatches.MatchMap')
        fields = ['id', 'rounds_won_team_a', 'rounds_won_team_b', 'starting_at', 'map_pick_of', 'played_map', 'map_nr']


class CSGOMatchSerializer(serializers.ModelSerializer):
    tournament = CSGOTournamentSerializer(read_only=True)
    lineup_a = CSGOLineupSerializer(read_only=True)
    lineup_b = CSGOLineupSerializer(read_only=True)
    livescore_url = serializers.SerializerMethodField(read_only=True, source='get_livescore_url')
    html_detail_url = serializers.SerializerMethodField(read_only=True, source='get_html_detail_url')
    last_map_end = serializers.SerializerMethodField(read_only=True, source='get_last_map_end')
    matchmaps = CSGOMatchMapSerializer(many=True, source='matchmap_set')
    block_voice_channel_display = serializers.SerializerMethodField(read_only=True, source='get_block_voice_channel_display')
    game = serializers.SerializerMethodField(read_only=True, source='get_game')
    has_ended = serializers.BooleanField(read_only=True)

    def get_livescore_url(self, obj):
        if obj.hltv_match_id:
            url = reverse('match_livescore-detail', kwargs={'pk': obj.hltv_match_id})
            request = self.context.get('request')
            return request.build_absolute_uri(url)

    def get_html_detail_url(self, obj):
        url = obj.get_absolute_url()
        request = self.context.get('request')
        return request.build_absolute_uri(url)

    def get_block_voice_channel_display(self, obj):
        return obj.get_block_voice_channel_display()

    def get_last_map_end(self, obj):
        last_map = obj.get_last_matchmap()
        if last_map:
            return last_map.starting_at + timezone.timedelta(hours=1)

    def get_game(self, obj):
        game = obj.get_game()
        if game:
            return game.name_short

    class Meta:
        model = apps.get_model('csgomatches.Match')
        fields = [
            'id', 'tournament', 'lineup_a', 'lineup_b', 'slug', 'bestof', 'game',
            'first_map_at', 'last_map_end', 'cancelled', 'hltv_match_id', 'esea_match_id', 'livescore_url', 'html_detail_url', 'matchmaps',
            'block_voice_channel_display', 'block_voice_channel', 'has_ended'
        ]


class CSGOMatchMapUpdateSerializer(serializers.ModelSerializer):
    played_map_name = serializers.CharField(max_length=206, write_only=True, required=False)

    def update(self, instance, validated_data):
        played_map_name = validated_data.pop('played_map_name', None)
        if played_map_name:
            played_map_obj = apps.get_model('csgomatches.Map').objects.filter(cs_name__iexact=played_map_name).first()
            if played_map_obj:
                instance.played_map = played_map_obj
        return super().update(instance, validated_data)


    class Meta:
        model = apps.get_model('csgomatches.MatchMap')
        fields = ['map_nr', 'rounds_won_team_a', 'rounds_won_team_b', 'unplayed', 'played_map_name']


class HLTVMapSerializer(serializers.Serializer):
    hltv_match_id = serializers.IntegerField()
    team_a_name = serializers.CharField(max_length=256, read_only=True)
    team_b_name = serializers.CharField(max_length=256, read_only=True)
    team_a_id = serializers.IntegerField(read_only=True)
    team_b_id = serializers.IntegerField(read_only=True)
    score_a = serializers.IntegerField(read_only=True)
    score_b = serializers.IntegerField(read_only=True)
    map_nr = serializers.IntegerField(read_only=True)
    map_name = serializers.CharField(max_length=256, read_only=True)


class HLTVMatchSerializer(serializers.Serializer):
    hltv_match_id = serializers.IntegerField()
    api_match_url = serializers.SerializerMethodField(read_only=True, source='get_api_match_url')
    team_a_name = serializers.CharField(max_length=256, read_only=True)
    team_a_id = serializers.IntegerField(read_only=True)
    team_b_name = serializers.CharField(max_length=256, read_only=True)
    team_b_id = serializers.IntegerField(read_only=True)
    maps = HLTVMapSerializer(many=True, read_only=True)
    team_id_to_name = serializers.DictField(read_only=True)
    name_to_team_id = serializers.DictField(read_only=True)

    def get_api_match_url(self, obj):
        if obj.hltv_match_id:
            csgo_match = apps.get_model('csgomatches.Match').objects.filter(hltv_match_id=obj.hltv_match_id).first()
            if csgo_match:
                url = reverse('match_all-detail', kwargs={'pk': csgo_match.pk})
                request = self.context.get('request')
                return request.build_absolute_uri(url)

    def create(self, validated_data):
        hltv_match_id = validated_data.get('hltv_match_id')
        inst = ser_objects.HLTVMatch(hltv_match_id=hltv_match_id)
        return inst


class FaceitProLeagueMatchesSerializer(serializers.Serializer):
    nr = serializers.IntegerField()
    players = serializers.ListField()
    streams = serializers.ListField()
    faceit_room_id = serializers.CharField()
    looked_up_nicknames = serializers.ListField()
    avatar = serializers.URLField()
    hub_name = serializers.CharField()
    hub_id = serializers.CharField()
    map = serializers.CharField()
    #roster1 = serializers.DictField()
    #roster2 = serializers.DictField()



