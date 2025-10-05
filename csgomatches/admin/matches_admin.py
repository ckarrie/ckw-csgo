from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from csgomatches.models import BaseOneOnOneMatch, CsMatch, BaseParticipant


@admin.register(BaseOneOnOneMatch)
class BaseOneOnOneMatchAdmin(PolymorphicParentModelAdmin):
	"""
	Parent admin for one-on-one matches. The base model itself should not be
	instantiated; instead the user is prompted to choose a concrete subtype.
	With only one child (CsMatch) Django-polymorphic will directly offer that
	option (or redirect to its add form depending on version).
	"""
	base_model = BaseOneOnOneMatch
	child_models = (CsMatch,)

@admin.register(CsMatch)
class CsMatchAdmin(PolymorphicChildModelAdmin):
	base_model = CsMatch

	list_display = (
		"participant_1",
		"participant_2",
		"starting_at",
		"match_type",
	)
	list_filter = ("match_type",)
	search_fields = (
		"participant_1__name",
		"participant_1__organization__name",
		"participant_2__name",
		"participant_2__organization__name",
		"slug",
	)
	ordering = ("-starting_at",)
	# Use autocomplete for participants so staff can search by name / org without exposing raw IDs.
	autocomplete_fields = ("participant_1", "participant_2", "win_condition_map")

	# Parameter set for the default CS2 map win condition (24 round MR12 + OT MR3, win by 2, no draw)
	DEFAULT_WIN_PARAMS = {
		"best_of_number": 24,
		"has_overtime": True,
		"has_draw": False,
		"best_of_number_overtime": 6,
		"win_by": 2,
	}

	def _get_default_win_condition(self):
		"""Fetch (by parameter set) or create the default BestOf win condition for CS matches.

		We intentionally ignore the name so an existing instance with a custom name
		but identical parameters is reused. If multiple exist, the earliest (lowest pk)
		is chosen to avoid duplication.
		"""
		from csgomatches.models import BestOfWinCondition  # local import to avoid circular
		qs = BestOfWinCondition.objects.filter(**self.DEFAULT_WIN_PARAMS).order_by("pk")
		obj = qs.first()
		if obj:
			return obj
		# Create without specifying name so model's save() assigns its canonical name.
		obj = BestOfWinCondition(**self.DEFAULT_WIN_PARAMS)
		obj.save()
		return obj

	def get_changeform_initial_data(self, request):
		initial = super().get_changeform_initial_data(request)
		# Only set if not provided; ignore errors silently so admin stays usable
		if "win_condition_map" not in initial:
			try:
				initial["win_condition_map"] = self._get_default_win_condition().pk
			except Exception:
				pass
		return initial

	def save_model(self, request, obj, form, change):
		# Ensure default win condition is applied if none chosen
		if not obj.win_condition_map_id:
			try:
				obj.win_condition_map = self._get_default_win_condition()
			except Exception:
				pass
		super().save_model(request, obj, form, change)


@admin.register(BaseParticipant)
class BaseParticipantAdmin(admin.ModelAdmin):
	"""Read-only style admin to support FK autocomplete lookups.

	We don't want staff to create bare BaseParticipant instances (they should use concrete
	player/lineup types), so we can disable add/delete while still allowing search.
	"""
	model = BaseParticipant
	search_fields = ("name", "organization__name")
	list_display = ("name", "organization", "game")
	ordering = ("name",)

	def get_search_results(self, request, queryset, search_term):
		"""Autocomplete policy:
		- Always show all CsLineup instances (unfiltered).
		- Only show CsPlayer instances once >=3 chars typed.
		- Preserve default matches for other participant subtypes (e.g. TrackMania) using the base search.

		Implementation detail: we avoid unioning different concrete model querysets (which can raise
		TypeError under polymorphic joins) by working only with the BaseParticipant queryset and
		filtering by the polymorphic content type IDs.
		"""
		from django.contrib.contenttypes.models import ContentType
		from csgomatches.models import CsLineup, CsPlayer

		# Get base filtered set (respects search_fields)
		base_qs, use_distinct = super().get_search_results(request, queryset, search_term)
		# Restrict everything to Counter-Strike participants only (game short name 'cs')
		# We apply this early so subsequent logic only considers CS objects.
		base_qs = base_qs.filter(game__name_short="cs")

		# Resolve content types for the concrete models we care about
		ct_lineup = ContentType.objects.get_for_model(CsLineup, for_concrete_model=False)
		ct_player = ContentType.objects.get_for_model(CsPlayer, for_concrete_model=False)

		# Start with all BaseParticipants restricted to: all lineups + (maybe) players + other matches from base_qs
		# 1. Always include all lineups
		lineup_ids = base_qs.model.objects.filter(polymorphic_ctype=ct_lineup).values_list("pk", flat=True)
		# If base_qs didn't include all lineups (because empty search), fetch remaining lineups directly
		# Using model manager ensures we stay within BaseParticipant.
		all_lineup_ids = base_qs.model.objects.filter(polymorphic_ctype=ct_lineup).values_list("pk", flat=True)
		lineup_ids = set(all_lineup_ids)

		# 2. Players: only if search term length >= 2 (take those matching base search)
		player_ids = set()
		if search_term and len(search_term) >= 2:
			player_ids = set(
				base_qs.model.objects.filter(polymorphic_ctype=ct_player, pk__in=base_qs.values_list("pk", flat=True))
				.values_list("pk", flat=True)
			)

		# 3. Other CS participant subtypes (if any in future) that matched original search (exclude lineup/player)
		other_ids = set(base_qs.exclude(polymorphic_ctype__in=[ct_lineup, ct_player]).values_list("pk", flat=True))

		final_ids = list(lineup_ids | player_ids | other_ids)
		final_qs = base_qs.model.objects.filter(pk__in=final_ids)
		return final_qs, use_distinct

	def has_add_permission(self, request):  # pragma: no cover - admin permission
		return False

	def has_delete_permission(self, request, obj=None):  # pragma: no cover
		return False
