import os
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def file_exists(static_path):
    file_path = os.path.join(settings.STATIC_ROOT, static_path)
    return os.path.exists(file_path)
