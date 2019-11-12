from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.decorators.cache import cache_page
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from . import feeds
from . import views

if settings.DEBUG:
    CACHE_INDEX_TIME = 0
    CACHE_ARCHIVE_TIME = 0
else:
    CACHE_INDEX_TIME = 1 * 60       # 1 Minute
    CACHE_ARCHIVE_TIME = 60 * 60    # 60 Minutes    1 Hour

sitemaps = {
    'upcoming': feeds.UpcomingMatchesSitemap,
    'history': feeds.ArchiveMatchesSitemap,
}

urlpatterns = [
    path(
        '',
        cache_page(timeout=CACHE_INDEX_TIME)(views.IndexView.as_view()),
        name="match_upcoming"
    ),
    path(
        'archive/<int:year>/',
        cache_page(timeout=CACHE_ARCHIVE_TIME)(views.YearArchiveView.as_view()),
        name="match_history"
    ),
    path(
        'feeds/big_upcoming.ics',
        cache_page(timeout=CACHE_INDEX_TIME)(feeds.UpcomingEventsFeed()),
        name='ics_upcoming_big'
    ),
    path(
        'admin/',
        admin.site.urls
    ),
    path('sitemap.xml', cache_page(CACHE_ARCHIVE_TIME)(sitemap), {
        'sitemaps': sitemaps,
        'template_name': 'csgomatches/feeds/google.xml'
    }, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap-google-news.xml', cache_page(CACHE_ARCHIVE_TIME)(sitemap), {
        'sitemaps': sitemaps,
        'template_name': 'csgomatches/feeds/google-news.xml'
    }, name='django.contrib.sitemaps.views.sitemap'),
    path(
        'robots.txt',
        TemplateView.as_view(template_name="csgomatches/feeds/robots.txt", content_type="text/plain"),
        name="robots_file"
    )
]
