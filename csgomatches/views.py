from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from . import models


class IndexView(generic.ListView):
    model = models.Match

    def get_queryset(self):
        qs = super(IndexView, self).get_queryset()
        qs = qs.filter(first_map_at__date__gte=timezone.now().date()).order_by('first_map_at')
        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super(IndexView, self).get_context_data(*args, **kwargs)
        ctx.update({
            'date_list': self.model.objects.all().dates('first_map_at', 'year'),
            'current_view': 'index'
        })
        return ctx


class YearArchiveView(generic.YearArchiveView):
    model = models.Match
    date_field = 'first_map_at'
    make_object_list = True
    allow_future = False


