from django.db import models

# Create your models here.
from django.utils import timezone


class Team(models.Model):
    name = models.CharField(max_length=255)
    name_long = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Player(models.Model):
    steam_id = models.CharField(max_length=255)
    ingame_name = models.CharField(max_length=255)
    ingame_name_long = models.CharField(max_length=255, null=True, blank=True)
    real_name = models.CharField(max_length=255)

    def __str__(self):
        return self.ingame_name


class PlayerRole(models.Model):
    name = models.CharField(max_length=255)
    # i.e. Fragger, Support, Leader, AWPer, Lurker, Coach

    def __str__(self):
        return self.name


class Lineup(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    team_logo_url = models.URLField(null=True, blank=True)
    active_from = models.DateTimeField()

    def __str__(self):
        return '{}'.format(self.team.name)


class LineupPlayer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    role = models.ForeignKey(PlayerRole, on_delete=models.CASCADE)
    lineup = models.ForeignKey(Lineup, on_delete=models.CASCADE)

    def __str__(self):
        return '{} ({})'.format(self.player.ingame_name, self.role.name)


class Tournament(models.Model):
    name = models.CharField(max_length=255)
    name_alt = models.CharField(max_length=255, null=True, blank=True)
    #mappool = models.ManyToManyField(Map)

    def __str__(self):
        return self.name


class Map(models.Model):
    name = models.CharField(max_length=255)
    cs_name = models.CharField(max_length=255, default='de_')

    def __str__(self):
        return self.name


class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    lineup_a = models.ForeignKey(Lineup, on_delete=models.CASCADE, related_name='matches_as_lineup_a_set', null=True, blank=True)
    lineup_b = models.ForeignKey(Lineup, on_delete=models.CASCADE, related_name='matches_as_lineup_b_set', null=True, blank=True)
    bestof = models.IntegerField(choices=(
        (1, 'BO1'),
        (2, 'BO2'),
        (3, 'BO3'),
        (5, 'BO5'),
    ))
    first_map_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.lineup_a and self.lineup_b:
            return '{} vs {}'.format(self.lineup_a.team.name, self.lineup_b.team.name)
        return '{} vs {}'.format('TBD', 'TBD')

    def get_first_matchmap(self):
        return self.matchmap_set.order_by('starting_at').first()


class MatchMap(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    played_map = models.ForeignKey(Map, on_delete=models.CASCADE, null=True, blank=True)
    rounds_won_team_a = models.IntegerField(default=0)
    rounds_won_team_b = models.IntegerField(default=0)
    starting_at = models.DateTimeField()
    delay_minutes = models.IntegerField(default=0)
    map_nr = models.IntegerField(null=True)
    map_pick_of = models.ForeignKey(Lineup, null=True, blank=True, on_delete=models.CASCADE)
    unplayed = models.BooleanField(default=False)
    #defwin_reason = models.CharField(max_length=255, null=True, blank=True)
    #defwin = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    def has_ended(self):
        return (self.rounds_won_team_a >= 16 or self.rounds_won_team_b >= 16) and abs(self.rounds_won_team_a - self.rounds_won_team_b) >= 2

    def is_live(self):
        has_ended = self.has_ended()
        if has_ended:
            return False
        calc_end = self.starting_at + timezone.timedelta(minutes=100)
        return self.starting_at < timezone.now() < calc_end

    def team_a_won(self):
        return (self.rounds_won_team_a > self.rounds_won_team_b) and (self.rounds_won_team_a >= 16 or self.rounds_won_team_b >= 16)

    def is_draw(self):
        return self.rounds_won_team_a == self.rounds_won_team_b

    def team_b_won(self):
        return (self.rounds_won_team_a < self.rounds_won_team_b) and (self.rounds_won_team_a >= 16 or self.rounds_won_team_b >= 16)

    def __str__(self):
        return '{} - {}'.format(self.match, self.starting_at)

    def save(self, *args, **kwargs):
        super(MatchMap, self).save(*args, **kwargs)
        first_matchmap = self.match.get_first_matchmap()
        if first_matchmap:
            self.match.first_map_at = first_matchmap.starting_at
            self.match.save()


class Cast(models.Model):
    matchmap = models.ForeignKey(MatchMap, on_delete=models.CASCADE)
    caster = models.CharField(max_length=255)
    stream_url = models.URLField()
    vod_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return '{}: {}'.format(self.caster, self.matchmap)









