from collections import OrderedDict

from django.db.models import Q
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.views import generic
from django.apps import apps

import random
import asyncio

from . import models

def get_random_background_image_url():
    images = [
        static("csgomatches/backgrounds/IMG_6232.JPG"),
        static("csgomatches/backgrounds/IMG_6239.JPG"),
        static("csgomatches/backgrounds/IMG_6412.JPG"),
    ]
    return random.choice(images)


class IndexView(generic.ListView):
    model = models.Match

    def get_queryset(self):
        qs = super(IndexView, self).get_queryset()
        qs = qs.filter(
            first_map_at__gte=timezone.now() - timezone.timedelta(hours=6),
        ).order_by('first_map_at')
        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super(IndexView, self).get_context_data(*args, **kwargs)
        big = models.Team.objects.get(name="BIG")
        statistics = {
            'last_sixteen_zero': models.MatchMap.objects.filter(
                match__lineup_a__team=big,
                rounds_won_team_a=16,
                rounds_won_team_b=0
            ).order_by('-starting_at').first(),
            'last_zero_sixteen': models.MatchMap.objects.filter(
                match__lineup_a__team=big,
                rounds_won_team_a=0,
                rounds_won_team_b=16
            ).order_by('-starting_at').first(),
            'last_sixteen_fourteen': models.MatchMap.objects.filter(
                match__lineup_a__team=big,
                rounds_won_team_a=16,
                rounds_won_team_b=14
            ).order_by('-starting_at').first(),
            'last_fourteen_sixteen': models.MatchMap.objects.filter(
                match__lineup_a__team=big,
                rounds_won_team_a=14,
                rounds_won_team_b=16
            ).order_by('-starting_at').first(),
        }
        ctx.update({
            'date_list': self.model.objects.all().dates('first_map_at', 'year', order='DESC'),
            'current_view': 'index',
            'bg_url': get_random_background_image_url(),
            'statistics': statistics
        })
        return ctx


class YearArchiveView(generic.YearArchiveView):
    model = models.Match
    date_field = 'first_map_at'
    make_object_list = True
    allow_future = False
    date_list_period = 'year'

    def get_date_list(self, queryset, date_type=None, ordering='ASC'):
        return self.model.objects.all().dates('first_map_at', 'year', order='DESC')

    def get_context_data(self, *args, **kwargs):
        ctx = super(YearArchiveView, self).get_context_data(*args, **kwargs)
        ctx.update({
            'bg_url': get_random_background_image_url()
        })
        return ctx

class MatchDetailView(generic.DetailView):
    model = models.Match

    def get_context_data(self, **kwargs):
        ctx = super(MatchDetailView, self).get_context_data(**kwargs)
        update = 0
        update_choices = [0, 10, 30, 60]
        if self.object.is_live():
            update = int(self.request.GET.get('update') or update_choices[1])
            if update not in update_choices:
                update = update_choices[0]
            self.object.update_hltv_livescore(request=self.request)
        elif self.object.is_upcoming():
            update = update_choices[-1]
        ctx.update({
            'score': self.object.get_overall_score(),
            'bg_url': get_random_background_image_url(),
            'update_seconds': update,
            'update_choices': update_choices
        })
        return ctx


class StaticPageDetailView(generic.DetailView):
    model = models.StaticPage

    def get_queryset(self):
        qs = super(StaticPageDetailView, self).get_queryset()
        qs = qs.filter(
            site=apps.get_model('sites.Site').objects.get_current()
        )
        return qs

    def get_template_names(self):
        return [self.object.get_template_name()]
