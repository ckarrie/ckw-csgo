from django.db import models


class TeamManager(models.Manager):
    def search_team(self, name):
        return self.filter(
            models.Q(name__iexact=name) |
            models.Q(name_long__iexact=name) |
            models.Q(name_alt__iexact=name)
        ).first()


class ExternalLinkManager(models.Manager):
    def visible(self):
        all_links = self.all()
        exclude_ids = []
        for link in all_links:
            if link.match.has_ended() and link.link_type == 'twitch_cast':
                exclude_ids.append(link.pk)

        if exclude_ids:
            return all_links.exclude(id__in=exclude_ids)
        return all_links


class LineupQuerySet(models.QuerySet):
    def search_lineups(self, name, hltv_id=None):
        # print("[LineupQuerySet] args=", name, hltv_id, type(hltv_id))
        if hltv_id:
            if isinstance(hltv_id, str) and hltv_id.isdigit():
                hltv_id = int(hltv_id)
            by_hltv_id = self.filter(team__hltv_id=hltv_id)
            # print("[LineupQuerySet] by_hltv_id", by_hltv_id)
            if by_hltv_id.exists():
                return by_hltv_id
        return self.filter(
            models.Q(team__name__iexact=name) |
            models.Q(team__name_long__iexact=name) |
            models.Q(team__name_alt__iexact=name)
        )

    def active_lineups(self, ref_dt=None):
        if ref_dt:
            # past matches with (maybe) older lineups
            return self.filter(active_from__lte=ref_dt).order_by('-active_from')
        return self.filter(is_active=True)
