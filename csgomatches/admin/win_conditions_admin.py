from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from csgomatches.models import BaseWinCondition, BestOfWinCondition, SimpleWinCondition

class BaseWinConditionAdmin(PolymorphicParentModelAdmin):
    base_model = BaseWinCondition
    child_models = (BestOfWinCondition, SimpleWinCondition)

class BestOfWinConditionAdmin(PolymorphicChildModelAdmin):
    base_model = BestOfWinCondition

class SimpleWinConditionAdmin(PolymorphicChildModelAdmin):
    base_model = SimpleWinCondition

admin.site.register(BaseWinCondition, BaseWinConditionAdmin)
admin.site.register(BestOfWinCondition, BestOfWinConditionAdmin)
admin.site.register(SimpleWinCondition, SimpleWinConditionAdmin)
