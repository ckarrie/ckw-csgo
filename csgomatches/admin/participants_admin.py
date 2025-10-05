from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from csgomatches.models import BasePlayer, CsPlayer, TrackManiaPlayer

class BasePlayersAdmin(PolymorphicChildModelAdmin, PolymorphicParentModelAdmin):
    base_model = BasePlayer
    child_models = (CsPlayer, TrackManiaPlayer)

class CsPlayerAdmin(PolymorphicChildModelAdmin):
    base_model = CsPlayer

class TrackManiaPlayerAdmin(PolymorphicChildModelAdmin):
    base_model = TrackManiaPlayer


admin.site.register(BasePlayer, BasePlayersAdmin)
admin.site.register(CsPlayer, CsPlayerAdmin)
admin.site.register(TrackManiaPlayer, TrackManiaPlayerAdmin)
