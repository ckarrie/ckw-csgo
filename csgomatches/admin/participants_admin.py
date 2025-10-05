from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from csgomatches.models import (
    BaseLineup,
    BasePlayer,
    CsLineup,
    CsPlayer,
    TrackManiaLineup,
    TrackManiaPlayer,
)


@admin.register(BasePlayer)
class BasePlayersAdmin(PolymorphicParentModelAdmin):
    base_model = BasePlayer
    child_models = (CsPlayer, TrackManiaPlayer)


class BasePlayerAdminForm(forms.ModelForm):
    lineup_field_name = "lineup"
    lineup_model = BaseLineup  # override in subclass

    class Meta:
        model = BasePlayer
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lineup_field = self.fields.get(self.lineup_field_name)
        if lineup_field and hasattr(self, "lineup_model") and self.lineup_model is not None:
            lineup_field.queryset = self.lineup_model.objects.all()
            if self.instance and self.instance.pk and self.instance.organization_id:
                lineup_field.queryset = lineup_field.queryset.filter(organization=self.instance.organization)

    def clean(self):
        cleaned = super().clean()
        lineup = cleaned.get(self.lineup_field_name)
        organization = cleaned.get("organization")
        if lineup:
            # type enforcement
            if self.lineup_model and not isinstance(lineup, self.lineup_model):
                self.add_error(self.lineup_field_name, f"Selected lineup is not a {self.lineup_model.__name__}.")
            if not organization:
                cleaned["organization"] = lineup.organization
            elif organization != lineup.organization:
                self.add_error("organization", "Organization must match the lineup's organization.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        lineup = getattr(obj, self.lineup_field_name, None)
        if lineup and not obj.organization:
            obj.organization = lineup.organization
        if lineup and not obj.game:
            obj.game = lineup.game
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class PlayerAdminMixin:
    form = BasePlayerAdminForm
    readonly_fields = ("display_game",)
    base_model = BasePlayer
    # 'game' is non-editable; expose only via display_game
    fields = ("name", "first_name", "last_name", "organization", "lineup", "display_game")
    lineup_model = None  # override

    def get_form(self, request, obj=None, **kwargs):
        # Create a dynamic subclass binding the lineup_model
        form_class = super().get_form(request, obj, **kwargs)
        # If base form used, inject lineup_model
        if hasattr(form_class, "lineup_model") and self.lineup_model:
            form_class.lineup_model = self.lineup_model
        return form_class

    def display_game(self, obj):
        return obj.game.name_short if obj and obj.game else "-"
    display_game.short_description = "Game"


@admin.register(CsPlayer)
class CsPlayerAdmin(PlayerAdminMixin, PolymorphicChildModelAdmin):
    base_model = CsPlayer
    lineup_model = CsLineup


@admin.register(TrackManiaPlayer)
class TrackManiaPlayerAdmin(PlayerAdminMixin, PolymorphicChildModelAdmin):
    base_model = TrackManiaPlayer
    lineup_model = TrackManiaLineup


@admin.register(BaseLineup)
class BaseLineupAdmin(PolymorphicParentModelAdmin):
    base_model = BaseLineup
    child_models = (CsLineup, TrackManiaLineup)


class BaseLineupAdminForm(forms.ModelForm):
    existing_players = forms.ModelMultipleChoiceField(
        queryset=BasePlayer.objects.none(),
        required=False,
        widget=FilteredSelectMultiple("Existing Players", is_stacked=False),
        help_text="Select players that should belong to this lineup. Unselect to detach."
    )
    new_players = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "One nickname per line or nickname|First|Last"}),
        help_text="Create and attach new players. One per line. Optional format: nickname|First|Last",
        label="Add New Players",
    )

    player_model = BasePlayer  # override
    game_short = None  # override (e.g. "cs")

    class Meta:
        model = BaseLineup
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.organization_id:
            base_qs = self.player_model.objects.filter(
                organization=self.instance.organization,
            )
            if self.game_short:
                base_qs = base_qs.filter(game__name_short=self.game_short)
            self.fields["existing_players"].queryset = base_qs
            self.initial["existing_players"] = list(
                base_qs.filter(lineup=self.instance).values_list("pk", flat=True)
            )
        else:
            qs = self.player_model.objects.filter(lineup__isnull=True)
            if self.game_short:
                qs = qs.filter(game__name_short=self.game_short)
            self.fields["existing_players"].queryset = qs


class BaseGameLineupAdmin(admin.ModelAdmin):
    form = BaseLineupAdminForm
    player_model = BasePlayer
    game_short = None
    search_fields = ("name", "organization__name", "slug")
    ordering = ("name",)

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)
        if hasattr(form_class, "player_model"):
            form_class.player_model = self.player_model
            form_class.game_short = self.game_short
        return form_class

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not hasattr(form, "cleaned_data"):
            return
        raw_new = form.cleaned_data.get("new_players") or ""
        created_new = []
        if raw_new.strip():
            for line in raw_new.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                nickname = parts[0]
                first = parts[1] if len(parts) > 1 else None
                last = parts[2] if len(parts) > 2 else None
                player = self.player_model(
                    name=nickname,
                    first_name=first or None,
                    last_name=last or None,
                    lineup=obj,
                    organization=obj.organization,
                    game=obj.game,
                )
                player.save()
                created_new.append(player)
        if created_new:
            self.message_user(request, f"Created {len(created_new)} new player(s).")
        selected = set(form.cleaned_data.get("existing_players") or [])
        current = set(self.player_model.objects.filter(lineup=obj))
        for p in created_new:
            selected.add(p)
        to_detach = current - selected
        to_attach = selected - current
        for player in to_detach:
            player.lineup = None
            player.save()
        for player in to_attach:
            player.lineup = obj
            player.organization = obj.organization
            player.game = obj.game
            player.save()
        if to_detach:
            self.message_user(request, f"Detached {len(to_detach)} player(s) via selection update.")
        if to_attach:
            self.message_user(request, f"Attached {len(to_attach)} player(s) via selection update.")


@admin.register(CsLineup)
class CsLineupAdmin(BaseGameLineupAdmin):
    base_model = CsLineup
    player_model = CsPlayer
    game_short = "cs"


@admin.register(TrackManiaLineup)
class TrackManiaLineupAdmin(BaseGameLineupAdmin):
    base_model = TrackManiaLineup
    player_model = TrackManiaPlayer
    game_short = "tm"
