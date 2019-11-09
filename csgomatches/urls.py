from django.contrib import admin
from django.urls import path
from django.views.decorators.cache import cache_page
from django.conf import settings

from . import views
from . import feeds

if settings.DEBUG:
    CACHE_INDEX_TIME = 0
    CACHE_ARCHIVE_TIME = 0
else:
    CACHE_INDEX_TIME = 1*60
    CACHE_ARCHIVE_TIME = 10*60

urlpatterns = [
    path('', cache_page(timeout=CACHE_INDEX_TIME)(views.IndexView.as_view()), name="match_upcoming"),
    path('archive/<int:year>/', cache_page(timeout=CACHE_ARCHIVE_TIME)(views.YearArchiveView.as_view()), name="match_history"),
    path('feeds/big_upcoming.ics', feeds.UpcomingEventsFeed(), name='ics_upcoming_big'),
    path('admin/', admin.site.urls),
]
