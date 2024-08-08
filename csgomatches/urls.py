from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.cache import cache_page
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from csgomatches.drf_api.urls import router
api_urlpatterns = router.urls
from . import feeds
from . import views

if settings.DEBUG:
    CACHE_INDEX_TIME = 0
    CACHE_MATCHDETAIL_TIME = 0
    CACHE_ARCHIVE_TIME = 0
else:
    CACHE_INDEX_TIME = 1 * 60       # 1 Minute
    CACHE_MATCHDETAIL_TIME = 10     # 10 Seconds
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
        'live/',
        cache_page(timeout=CACHE_INDEX_TIME)(views.LiveStreamsView.as_view()),
        name="livestreams"
    ),
    path(
        'archive/<int:year>/',
        cache_page(timeout=CACHE_ARCHIVE_TIME)(views.YearArchiveView.as_view()),
        name="match_history"
    ),
    path(
        '<slug:slug>',
        cache_page(timeout=CACHE_MATCHDETAIL_TIME)(views.MatchDetailView.as_view()),
        name="match_details"
    ),
    path(
        'feeds/big_upcoming.ics',
        cache_page(timeout=CACHE_INDEX_TIME)(feeds.UpcomingEventsFeed()),
        name='ics_upcoming_big'
    ),
    # FilteredUpcomingEventsFeed
    path(
        'feeds/big_upcoming_cs.ics',
        cache_page(timeout=CACHE_INDEX_TIME)(feeds.FilteredUpcomingEventsFeed()),
        name='ics_upcoming_big_cs'
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
    ),
    path(
        's/<slug:slug>',
        cache_page(timeout=CACHE_ARCHIVE_TIME)(views.StaticPageDetailView.as_view()),
        name='staticpage'
    ),
    path('api/', include(router.urls), ),
]

if 'permabots' in settings.INSTALLED_APPS:
    urlpatterns +=[
        path('bot/', include('permabots.urls_processing', namespace='permabots'), ),
    ]

#urlpatterns += api_urlpatterns
