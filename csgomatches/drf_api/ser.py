from django.urls import reverse
from rest_framework import serializers
from django.apps import apps

from . import ser_objects
from csgomatches.models.cs_models import CSLineupPlayerRole

class CsTournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.CsTournament')
        fields = ['name', 'name_alt', 'name_hltv', 'name_99dmg', 'id']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.Team')
        fields = ['name', 'name_long', 'name_alt', 'hltv_id', 'id']


class CsPlayerShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.CsPlayer')
        fields = ['ingame_name',]

class CSGOLineupPlayerSerializer(serializers.ModelSerializer):
    player = CSGOPlayerShortSerializer()
    role = serializers.SerializerMethodField()

    class Meta:
        model = apps.get_model('csgomatches.CsLineupPlayer')
        fields = ['player', 'role']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Map the enum value to a more human-readable string
        representation['role'] = CSLineupPlayerRole(instance.role).name if instance.role else None
        return representation

    def to_internal_value(self, data):
        # Convert string to enum value during deserialization
        internal_value = super().to_internal_value(data)
        role = data.get('role')

        if role is not None:
            try:
                internal_value['role'] = CSLineupPlayerRole[role].value
            except KeyError:
                raise serializers.ValidationError(f"Invalid role: {role}")
        return internal_value


class CsLineupSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    players = CsLineupPlayerSerializer(many=True, read_only=True, source='lineupplayer_set')

    class Meta:
        model = apps.get_model('csgomatches.CsLineup')
        fields = ['team', 'team_logo_url', 'active_from', 'players', 'id']

class CsMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.CsMap')
        fields = ['name', 'cs_name', 'id']

class CsMatchMapSerializer(serializers.ModelSerializer):
    map_pick_of = CsLineupSerializer(read_only=True)
    played = CsMapSerializer(read_only=True)

    class Meta:
        model = apps.get_model('csgomatches.CsMatchMap')
        fields = ['rounds_won_team_a', 'rounds_won_team_b', 'starting_at', 'map_pick_of', 'map', 'id']


class CsMatchSerializer(serializers.ModelSerializer):
    tournament = CsTournamentSerializer(read_only=True)
    lineup_a = CsLineupSerializer(read_only=True)
    lineup_b = CsLineupSerializer(read_only=True)
    livescore_url = serializers.SerializerMethodField(read_only=True, source='get_livescore_url')
    html_detail_url = serializers.SerializerMethodField(read_only=True, source='get_html_detail_url')
    matchmaps = CsMatchMapSerializer(many=True, source='matchmap_set')

    def get_livescore_url(self, obj):
        if obj.hltv_match_id:
            url = reverse('match_livescore-detail', kwargs={'pk': obj.hltv_match_id})
            request = self.context.get('request')
            return request.build_absolute_uri(url) # type: ignore

    def get_html_detail_url(self, obj):
        url = obj.get_absolute_url()
        request = self.context.get('request')
        return request.build_absolute_uri(url) # type: ignore

    class Meta:
        model = apps.get_model('csgomatches.CsMatch')
        fields = ['tournament', 'lineup_a', 'lineup_b', 'slug', 'bestof', 'first_map_at', 'cancelled', 'hltv_match_id', 'livescore_url', 'html_detail_url', 'matchmaps']


class CsMatchMapUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model('csgomatches.CsMatchMap')
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
                return request.build_absolute_uri(url) # type: ignore

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



