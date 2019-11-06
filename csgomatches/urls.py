from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name="match_upcoming"),
    path('archive/<int:year>/', views.YearArchiveView.as_view(), name="match_history"),
    path('admin/', admin.site.urls),
]
