from django.db.models import Q
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.views import generic

import random

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
        ctx.update({
            'date_list': self.model.objects.all().dates('first_map_at', 'year', order='DESC'),
            'current_view': 'index',
            'bg_url': get_random_background_image_url()
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
        ctx.update({
            'score': self.object.get_overall_score(),
            'bg_url': get_random_background_image_url()
        })
        return ctx

