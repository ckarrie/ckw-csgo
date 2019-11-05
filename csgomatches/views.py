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


