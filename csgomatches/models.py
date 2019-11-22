from django.db import models
from django.contrib.sites.models import Site

# Create your models here.
from django.template import defaultfilters
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Team(models.Model):
    name = models.CharField(max_length=255)
    name_long = models.CharField(max_length=255, null=True, blank=True)
    name_alt = models.CharField(max_length=255, null=True, blank=True)

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

    class Meta:
        ordering = ['team__name', '-active_from']


class LineupPlayer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    role = models.ForeignKey(PlayerRole, on_delete=models.CASCADE)
    lineup = models.ForeignKey(Lineup, on_delete=models.CASCADE)

    def __str__(self):
        return '{} ({})'.format(self.player.ingame_name, self.role.name)


class Tournament(models.Model):
    name = models.CharField(max_length=255)
    name_alt = models.CharField(max_length=255, null=True, blank=True)
    name_hltv = models.CharField(max_length=255, null=True, blank=True)
    name_99dmg = models.CharField(max_length=255, null=True, blank=True)
    #mappool = models.ManyToManyField(Map)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Map(models.Model):
    name = models.CharField(max_length=255)
    cs_name = models.CharField(max_length=255, default='de_')

    def __str__(self):
        return self.name


class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True, allow_unicode=False, null=True, blank=True, max_length=255)
    lineup_a = models.ForeignKey(Lineup, on_delete=models.CASCADE, related_name='matches_as_lineup_a_set', null=True, blank=True)
    lineup_b = models.ForeignKey(Lineup, on_delete=models.CASCADE, related_name='matches_as_lineup_b_set', null=True, blank=True)
    bestof = models.IntegerField(choices=(
        (1, 'BO1'),
        (2, 'BO2'),
        (3, 'BO3'),
        (5, 'BO5'),
    ))
    first_map_at = models.DateTimeField(null=True, blank=True)
    cancelled = models.IntegerField(
        default=0,
        choices=(
            (0, 'normal'),
            (1, 'Defwin in favour of team A'),
            (2, 'Defwin in favour of team B'),
        )
    )

    def __str__(self):
        if self.lineup_a and self.lineup_b:
            return '{} vs {}'.format(self.lineup_a.team.name, self.lineup_b.team.name)
        return '{} vs {}'.format('TBD', 'TBD')

    def get_first_matchmap(self):
        return self.matchmap_set.order_by('starting_at').first()

    def is_live(self):
        if self.has_ended():
            return False
        return self.first_map_at < timezone.now()

    def has_ended(self):
        if self.cancelled > 0:
            return True
        last_map = self.matchmap_set.order_by('map_nr').last()
        if last_map:
            if last_map.has_ended():
                return True
            #if last_map.starting_at
        team_a, team_b = self.get_overall_score()
        if team_a > team_b or team_b > team_a:
            return True
        return False

    def get_overall_score(self):
        lineup_a_mapwins = 0
        lineup_b_mapwins = 0
        for mm in self.matchmap_set.all():
            if mm.has_ended():
                if mm.team_a_won():
                    lineup_a_mapwins += 1
                if mm.team_b_won():
                    lineup_b_mapwins += 1
        return (lineup_a_mapwins, lineup_b_mapwins)

    def team_a_won(self):
        if self.cancelled == 1:
            return True
        t_a, t_b = self.get_overall_score()
        return t_a > t_b

    def team_b_won(self):
        if self.cancelled == 2:
            return True
        t_a, t_b = self.get_overall_score()
        return t_a < t_b

    def is_draw(self):
        t_a, t_b = self.get_overall_score()
        return t_a == t_b
    
    def save(self, *args, **kwargs):
        similar_matches_in_same_tournament = self.tournament.match_set.filter(
            lineup_a=self.lineup_a, lineup_b=self.lineup_b
        )
        if similar_matches_in_same_tournament.exclude(pk=self.pk).exists():
            idx = list(similar_matches_in_same_tournament).index(self)
            self.slug = slugify("{}-{}-{}".format(self.tournament.name, self, idx))
        else:
            self.slug = slugify("{}-{}".format(self.tournament.name, self))
        existing_slugs = Match.objects.filter(slug=self.slug).exclude(pk=self.pk)
        if existing_slugs.exists():
            self.slug = slugify("id-{}".format(self.pk))
        super(Match, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('match_details', kwargs={'slug': self.slug})

    class Meta:
        ordering = ['-first_map_at']


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

    def get_prev_map(self):
        return self.match.matchmap_set.filter(map_nr__lt=self.map_nr).order_by('map_nr').last()

    def get_next_map(self):
        return self.match.matchmap_set.filter(map_nr__gt=self.map_nr).order_by('map_nr').first()

    def has_ended(self):
        return (self.rounds_won_team_a >= 16 or self.rounds_won_team_b >= 16) and abs(self.rounds_won_team_a - self.rounds_won_team_b) >= 2

    def is_live(self):
        prev = self.get_prev_map()
        if prev and prev.is_live():
            return False
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
        return '{} - {} Map #{}'.format(self.match, self.starting_at.date(), self.map_nr)

    def save(self, *args, **kwargs):
        super(MatchMap, self).save(*args, **kwargs)
        first_matchmap = self.match.get_first_matchmap()
        if first_matchmap:
            self.match.first_map_at = first_matchmap.starting_at
            self.match.save()

    class Meta:
        ordering = ['starting_at']

class ExternalLinkManager(models.Manager):
    def visible(self):
        all_links = self.all()
        exclude_ids = []
        for link in all_links:
            if link.match.has_ended() and link.link_type == 'twitch_cast':
                exclude_ids.append(link.pk)

        if exclude_ids:
            return all_links.exclude(id__in=exclude_ids)
        return all_links

class ExternalLink(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    link_type = models.CharField(max_length=255, choices=(
        ('hltv_match', 'HLTV'),
        ('hltv_demo', 'Demo'),
        ('99dmg_match', '99DMG'),
        ('twitch_cast', 'Cast'),
        ('twitch_vod', 'VOD'),
        ('youtube_vod', 'VOD'),
    ))
    link_flag = models.CharField(max_length=3, default='en')
    title = models.CharField(max_length=255)
    url = models.URLField()
    objects = ExternalLinkManager()

    def get_flag_url(self):
        return 'csgomatches/flags/{}.png'.format(self.link_flag)

    def __str__(self):
        return '{}: {}'.format(self.title, self.match)

    class Meta:
        ordering = ['match', 'link_flag', 'link_type']


class CSGOSiteSetting(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    main_team = models.ForeignKey('csgomatches.Team', on_delete=models.CASCADE, related_name='main_team_settings')
    second_team = models.ForeignKey('csgomatches.Team', on_delete=models.CASCADE, related_name='sec_team_settings')

    class Meta:
        unique_together = ['site', 'main_team', 'second_team']






