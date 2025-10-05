from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from csgomatches.models import BaseWinCondition, BestOfWinCondition, SimpleWinCondition

@admin.register(BaseWinCondition)
class BaseWinConditionAdmin(PolymorphicParentModelAdmin):
    base_model = BaseWinCondition
    child_models = (BestOfWinCondition, SimpleWinCondition)
    search_fields = ("name",)

@admin.register(BestOfWinCondition)
class BestOfWinConditionAdmin(PolymorphicChildModelAdmin):
    base_model = BestOfWinCondition

@admin.register(SimpleWinCondition)
class SimpleWinConditionAdmin(PolymorphicChildModelAdmin):
    base_model = SimpleWinCondition
