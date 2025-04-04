from django.urls import reverse
from rest_framework import serializers
from django.apps import apps

from . import ser_objects

class CSGOTournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.Tournament')
        fields = ['name', 'name_alt', 'name_hltv', 'name_99dmg', 'id']


class CSGOTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.Team')
        fields = ['name', 'name_long', 'name_alt', 'hltv_id', 'id']


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
        fields = ['team', 'team_logo_url', 'active_from', 'players', 'id']

class CSGOMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.Map')
        fields = ['name', 'cs_name', 'id']

class CSGOMatchMapSerializer(serializers.ModelSerializer):
    map_pick_of = CSGOLineupSerializer(read_only=True)
    played_map = CSGOMapSerializer(read_only=True)

    class Meta:
        model = apps.get_model('csgomatches.MatchMap')
        fields = ['rounds_won_team_a', 'rounds_won_team_b', 'starting_at', 'map_pick_of', 'played_map', 'id']


class CSGOMatchSerializer(serializers.ModelSerializer):
    tournament = CSGOTournamentSerializer(read_only=True)
    lineup_a = CSGOLineupSerializer(read_only=True)
    lineup_b = CSGOLineupSerializer(read_only=True)
    livescore_url = serializers.SerializerMethodField(read_only=True, source='get_livescore_url')
    html_detail_url = serializers.SerializerMethodField(read_only=True, source='get_html_detail_url')
    matchmaps = CSGOMatchMapSerializer(many=True, source='matchmap_set')

    def get_livescore_url(self, obj):
        if obj.hltv_match_id:
            url = reverse('match_livescore-detail', kwargs={'pk': obj.hltv_match_id})
            request = self.context.get('request')
            return request.build_absolute_uri(url)

    def get_html_detail_url(self, obj):
        url = obj.get_absolute_url()
        request = self.context.get('request')
        return request.build_absolute_uri(url)

    class Meta:
        model = apps.get_model('csgomatches.Match')
        fields = ['tournament', 'lineup_a', 'lineup_b', 'slug', 'bestof', 'first_map_at', 'cancelled', 'hltv_match_id', 'livescore_url', 'html_detail_url', 'matchmaps']


class CSGOMatchMapUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.MatchMap')
        fields = ['map_nr', 'rounds_won_team_a', 'rounds_won_team_b',]


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



