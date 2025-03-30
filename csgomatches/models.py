import os
import requests
import twitter
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import QuerySet
# Create your models here.
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from . import managers
from .utils.publishing import twitter_api


def get_flags_choices()-> list[tuple[str, str]]:
    """
    returns a list of tuples of all available flags by looking at png files in 'static/csgomatches/flags'
    """
    choices: list[tuple[str, str]] = []
    base_pth = os.path.dirname(os.path.abspath(__file__))
    flags_pth = os.path.join(base_pth, 'static/csgomatches/flags')
    for fn in os.listdir(flags_pth):
        if fn.endswith('.png'):
            short_fn = fn.replace('.png', '')
            choices.append((short_fn, short_fn))
    choices.sort(key=lambda x: x[0])
    return choices


class Game(models.Model):
    name = models.CharField(max_length=255, help_text='i.e. "TrackMania" or "Counter-Strike"')
    name_short = models.CharField(max_length=4, help_text='i.e. "tm", "cs"')
    game_logo_url = models.URLField(null=True, blank=True)
    game_logo_width = models.IntegerField(null=True, blank=True, help_text="i.e. 50 for 50px")
    slug = models.SlugField()

    def __str__(self):
        return self.name


class Team(models.Model):
    #game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    name_long = models.CharField(max_length=255, null=True, blank=True)
    name_alt = models.CharField(max_length=255, null=True, blank=True)
    hltv_id = models.IntegerField(null=True, blank=True)
    esea_team_id = models.IntegerField(null=True, blank=True)

    lineup_set: QuerySet['Lineup']

    objects = managers.TeamManager()

    def get_hltv_id_from_name(self):
        from .utils.scrapers.hltv import get_hltv_id_from_team_name
        return get_hltv_id_from_team_name(team_mdl=self)

    def get_hltv_team_link(self):
        if self.hltv_id:
            return f'https://www.hltv.org/team/{self.hltv_id}/team'

    def __str__(self):
        #if self.game:
        #    return '[{game}] {name}'.format(game=self.game, name=self.name)
        return self.name


class Player(models.Model):
    steam_id = models.CharField(max_length=255, null=True, blank=True)
    ingame_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    hltv_id = models.IntegerField(null=True, blank=True)
    esea_user_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} "{self.ingame_name}" {self.last_name}'


class PlayerRole(models.Model):
    name = models.CharField(max_length=255)

    # i.e. Fragger, Support, Leader, AWPer, Lurker, Coach

    def __str__(self):
        return self.name


class Lineup(models.Model):
    game = models.ForeignKey(Game, null=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    team_logo_url = models.URLField(null=True, blank=True)
    active_from = models.DateTimeField(help_text='Set -10 Days to avoid multiple Lineup creations')
    is_active = models.BooleanField(default=True)

    objects = managers.LineupQuerySet.as_manager()

    def get_previous_lineup(self) -> 'Lineup | None':
        return self.team.lineup_set.filter(
            active_from__lt=self.active_from
        ).order_by('-active_from').first()

    def get_next_lineup(self) -> 'Lineup | None':
        return self.team.lineup_set.filter(
            active_from__gt=self.active_from
        ).order_by('active_from').first()

    def get_is_active(self):
        next_lu = self.get_next_lineup()
        if next_lu:
            return False
        return True

    def __str__(self):
        if self.game:
            return f'[{self.game.name}] {self.team.name}'
        return f'{self.team.name}'

    def save(self, *args, **kwargs):
        next_lu = self.get_next_lineup()
        if next_lu:
            self.is_active = False
        prev_lu = self.get_previous_lineup()
        if prev_lu:
            prev_lu.is_active = False
            prev_lu.save()
        super(Lineup, self).save(*args, **kwargs)

    class Meta:
        ordering = ['team__name', '-active_from']
        unique_together = ('team', 'active_from')


class LineupPlayer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    role = models.ForeignKey(PlayerRole, on_delete=models.CASCADE, null=True, blank=True)
    lineup = models.ForeignKey(Lineup, on_delete=models.CASCADE)

    def __str__(self):
        if self.role:
            return f'{self.player.ingame_name} ({self.role.name})'
        return f'{self.player.ingame_name} @ {self.lineup.team.name}'


class Tournament(models.Model):
    name = models.CharField(max_length=255)
    name_alt = models.CharField(max_length=255, null=True, blank=True)
    name_hltv = models.CharField(max_length=255, null=True, blank=True)
    name_99dmg = models.CharField(max_length=255, null=True, blank=True)
    esea_bracket_id = models.IntegerField(null=True, blank=True)
    esea_bracket_team_ids = models.CharField(max_length=255, null=True, blank=True, help_text='Comma Separated')

    match_set: QuerySet['Match']

    # mappool = models.ManyToManyField(Map)

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
    description = models.TextField(null=True, blank=True, help_text='Text is mark_safe')
    cancelled = models.IntegerField(
        default=0,
        choices=(
            (0, 'normal'),
            (1, 'Defwin in favour of team A'),
            (2, 'Defwin in favour of team B'),
        )
    )
    hltv_match_id = models.CharField(max_length=20, null=True, blank=True, help_text='For HLTV Livescore during match')
    esea_match_id = models.CharField(max_length=255, null=True, blank=True)
    enable_tweet = models.BooleanField(default=False)
    last_tweet = models.DateTimeField(null=True, blank=True)
    last_tweet_id = models.CharField(max_length=255, null=True, blank=True)
    enable_99dmg = models.BooleanField(default=False)
    enable_hltv = models.BooleanField(default=True)

    matchmap_set: QuerySet['MatchMap']

    class Meta:
        ordering = ['-first_map_at']
        verbose_name_plural = "matches"

    def __str__(self) -> str:
        if self.lineup_a and self.lineup_b:
            return f'{self.lineup_a.team.name} vs {self.lineup_b.team.name}'
        elif self.lineup_a and not self.lineup_b:
            return f'{self.lineup_a.team.name}'
        return 'TBA vs TBA'

    def get_first_matchmap(self) -> 'MatchMap | None':
        return self.matchmap_set.order_by('starting_at').first()

    def is_live(self) -> bool | None:
        if self.has_ended():
            return False
        if not self.first_map_at:
            return None

        current_live_mms = []
        for mmap in self.matchmap_set.order_by('map_nr'):
            current_live_mms.append(mmap.is_live())
        if current_live_mms:
            return any(current_live_mms)

        return self.first_map_at < timezone.now()

    def has_ended(self) -> bool:
        if self.cancelled > 0:
            return True
        last_map = self.matchmap_set.order_by('map_nr').last()
        if last_map:
            if last_map.has_ended():
                return True
                # if last_map.starting_at
        team_a, team_b = self.get_overall_score()
        if team_a > team_b or team_b > team_a:
            return True
        return False

    def is_upcoming(self) -> bool | None:
        if self.first_map_at:
            return self.first_map_at > timezone.now()

    def get_overall_score(self) -> tuple[int, int]:
        lineup_a_mapwins = 0
        lineup_b_mapwins = 0
        for mm in self.matchmap_set.all():
            if mm.has_ended():
                if mm.team_a_won():
                    lineup_a_mapwins += 1
                if mm.team_b_won():
                    lineup_b_mapwins += 1
        return lineup_a_mapwins, lineup_b_mapwins

    def team_a_won(self) -> bool:
        if self.cancelled == 1:
            return True
        t_a, t_b = self.get_overall_score()
        return t_a > t_b

    def team_b_won(self) -> bool:
        if self.cancelled == 2:
            return True
        t_a, t_b = self.get_overall_score()
        return t_a < t_b

    def is_draw(self) -> bool:
        t_a, t_b = self.get_overall_score()
        return t_a == t_b

    def save(self, *args, **kwargs):
        similar_matches_in_same_tournament = self.tournament.match_set.filter(
            lineup_a=self.lineup_a,
            lineup_b=self.lineup_b,
            first_map_at=self.first_map_at
        )
        if similar_matches_in_same_tournament.exclude(pk=self.pk).exists():
            try:
                idx = list(similar_matches_in_same_tournament).index(self)
            except ValueError:
                # object was moved
                self.slug = slugify(f"id-{self.pk}")
            else:
                self.slug = slugify(f"{self.tournament.name}-{self}-{idx}")
        else:
            self.slug = slugify(f"{self.tournament.name}-{self}")
        existing_slugs = Match.objects.filter(slug=self.slug).exclude(pk=self.pk)
        if existing_slugs.exists():
            self.slug = slugify(f"id-{self.pk}")
        super(Match, self).save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse('match_details', kwargs={'slug': self.slug})

    def get_livescore_url(self, request):
        if self.hltv_match_id:
            url = reverse('match_livescore-detail', kwargs={'pk': self.hltv_match_id})
            return request.build_absolute_uri(url)

    def update_hltv_livescore(self, request) -> None:
        # Guard clause in case lineup_a is None
        if not self.lineup_a:
            return

        url = self.get_livescore_url(request=request)
        if url:
            response = requests.get(url=url, params={'format': 'json'}).json()
            maps = response.get('maps', [])
            for map_data in maps:
                map_nr = map_data.get('map_nr')
                mm_obj = self.matchmap_set.filter(map_nr=map_nr).first()
                if mm_obj:
                    mm_obj.played_map = Map.objects.filter(
                        models.Q(name=map_data.get('map_name')) |
                        models.Q(cs_name=map_data.get('map_name'))
                    ).first()
                    score_a, score_b = map_data.get('score_a'), map_data.get('score_b')
                    swap_score = False
                    team_a_hltv_id = response.get('team_a_id')
                    if team_a_hltv_id != self.lineup_a.team.hltv_id:
                        swap_score = True

                    if swap_score:
                        score_b, score_a = score_a, score_b

                    mm_obj.rounds_won_team_a = score_a
                    mm_obj.rounds_won_team_b = score_b
                    mm_obj.save()


class MatchMap(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    played_map = models.ForeignKey(Map, on_delete=models.CASCADE, null=True, blank=True)
    rounds_won_team_a = models.IntegerField(default=0)
    rounds_won_team_b = models.IntegerField(default=0)
    starting_at = models.DateTimeField()
    delay_minutes = models.IntegerField(default=0)
    map_nr = models.IntegerField(editable=False)
    map_pick_of = models.ForeignKey(Lineup, null=True, blank=True, on_delete=models.CASCADE)
    unplayed = models.BooleanField(default=False)
    # defwin_reason = models.CharField(max_length=255, null=True, blank=True)
    # defwin = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    def get_prev_map(self) -> 'MatchMap | None':
        return self.match.matchmap_set.filter(map_nr__lt=self.map_nr).order_by('map_nr').last()

    def get_next_map(self) -> 'MatchMap | None':
        return self.match.matchmap_set.filter(map_nr__gt=self.map_nr).order_by('map_nr').first()

    def has_ended(self) -> bool:
        return (self.rounds_won_team_a >= 13 or self.rounds_won_team_b >= 13) and abs(self.rounds_won_team_a - self.rounds_won_team_b) >= 2

    def is_live(self):
        prev = self.get_prev_map()
        if prev and prev.is_live():
            return False
        has_ended = self.has_ended()
        if has_ended:
            return False
        calc_end = self.starting_at + timezone.timedelta(minutes=100)
        return self.starting_at < timezone.now() < calc_end

    def team_a_won(self) -> bool:
        return (self.rounds_won_team_a > self.rounds_won_team_b) and (self.rounds_won_team_a >= 13 or self.rounds_won_team_b >= 13)

    def is_draw(self) -> bool:
        return self.rounds_won_team_a == self.rounds_won_team_b

    def team_b_won(self) -> bool:
        return (self.rounds_won_team_a < self.rounds_won_team_b) and (self.rounds_won_team_a >= 13 or self.rounds_won_team_b >= 13)

    def __str__(self):
        return f'{self.match} - {self.starting_at.date()} Map #{self.map_nr} (ID = {self.pk if self.pk else "-"})'

    def send_tweet(self, prev_instance=None, interval=180.) -> None:
        # Guard clause in case either lineup_a or lineup_b are None
        if not self.match.lineup_a or not self.match.lineup_b:
            return

        if self.match.enable_tweet and prev_instance:
            if prev_instance.rounds_won_team_a != self.rounds_won_team_a or prev_instance.rounds_won_team_b != self.rounds_won_team_b:
                print(f"[MatchMap.save] Score changed {prev_instance.rounds_won_team_a}:{prev_instance.rounds_won_team_b}"
                      " -> {self.rounds_won_team_a}:{self.rounds_won_team_b}")
                tweet_dict = {
                    'team_a': self.match.lineup_a.team.name,
                    'team_b': self.match.lineup_b.team.name,
                    'score_a': self.rounds_won_team_a,
                    'score_b': self.rounds_won_team_b,
                    'map_nr': self.map_nr,
                    'map_name': self.played_map.name if self.played_map else "-",
                    'tournament': self.match.tournament.name,
                    'slug': self.match.get_absolute_url()
                }

                if not self.match.last_tweet:
                    # set this after first round (first save)
                    self.match.last_tweet = timezone.now()
                    self.match.save()

                if (timezone.now() - self.match.last_tweet).total_seconds() > interval:
                    consumer_key, consumer_secret, access_token_key, access_token_secret = twitter_api.get_twitter_credentials()
                    api = twitter.Api(consumer_key=consumer_key,
                                      consumer_secret=consumer_secret,
                                      access_token_key=access_token_key,
                                      access_token_secret=access_token_secret)

                    tweet_text = "{team_a} {score_a}:{score_b} {team_b}\n" \
                                 "\n" \
                                 "Map #{map_nr} ({map_name})\n" \
                                 "{tournament}\n" \
                                 "\n" \
                                 "More at https://wannspieltbig.de{slug}".format(**tweet_dict)

                    print(f"Posting to {len(api.GetFollowerIDs())} followers")
                    in_reply_to_status_id = self.match.last_tweet_id
                    tw_status: twitter.Status = api.PostUpdate(
                        status=tweet_text,
                        in_reply_to_status_id=in_reply_to_status_id
                    )
                    self.match.last_tweet_id = str(tw_status.id) # type: ignore
                    self.match.last_tweet = timezone.now()
                    self.match.save()

    def save(self, *args, **kwargs):
        prev_instance = None
        if self.pk:
            prev_instance = MatchMap.objects.get(pk=self.pk)
        if not self.map_nr:  # Only set map_nr if it's not already assigned
            last_map = self.match.matchmap_set.order_by('-map_nr').first()
            self.map_nr = (last_map.map_nr + 1) if last_map else 1

        super(MatchMap, self).save(*args, **kwargs)
        first_matchmap = self.match.get_first_matchmap()
        if first_matchmap:
            self.match.first_map_at = first_matchmap.starting_at
            self.match.save()
        self.send_tweet(prev_instance=prev_instance)

    class Meta:
        ordering = ['starting_at']


class ExternalLink(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    link_type = models.CharField(max_length=255, choices=(
        ('hltv_match', 'HLTV'),
        ('esea_match', 'ESEA Match'),
        ('esea_event', 'ESEA Event'),
        ('hltv_demo', 'Demo'),
        ('99dmg_match', '99DMG'),
        ('twitch_cast', 'Cast'),
        ('twitch_vod', 'Twitch VOD'),
        ('youtube_vod', 'YouTube VOD'),
        ('link', 'Link'),
    ))
    link_flag = models.CharField(
        max_length=50, default='en', help_text='see ckw-csgo/csgomatches/static/csgomatches/flags',
        choices=get_flags_choices()
    )
    title = models.CharField(max_length=255)
    url = models.URLField()
    objects = managers.ExternalLinkManager()

    def get_flag_url(self) -> str:
        return f'csgomatches/flags/{self.link_flag}.png'

    def __str__(self):
        return '{self.title}: {self.match}'

    class Meta:
        ordering = ['match', 'link_flag', 'link_type']


class CSGOSiteSetting(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    main_team = models.ForeignKey('csgomatches.Team', on_delete=models.CASCADE, related_name='main_team_settings')
    second_team = models.ForeignKey('csgomatches.Team', on_delete=models.CASCADE, related_name='sec_team_settings')
    site_teams = models.ManyToManyField('csgomatches.Team')

    class Meta:
        unique_together = ['site', 'main_team', 'second_team']


class StaticPage(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True, allow_unicode=False, max_length=255)
    template_name = models.CharField(max_length=255, default='default.html')

    def get_template_name(self) -> str:
        return f'csgomatches/staticpages/{self.template_name}'
