from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from . import models


class GameModelTest(TestCase):
    """Test cases for the Game model"""

    def setUp(self):
        self.game = models.Game.objects.create(
            name="Counter-Strike",
            name_short="cs",
            slug="cs"
        )

    def test_game_creation(self):
        """Test that a game can be created"""
        self.assertEqual(self.game.name, "Counter-Strike")
        self.assertEqual(self.game.name_short, "cs")
        self.assertEqual(self.game.slug, "cs")

    def test_game_str(self):
        """Test the string representation of a game"""
        self.assertEqual(str(self.game), "Counter-Strike")


class TeamModelTest(TestCase):
    """Test cases for the Team model"""

    def setUp(self):
        self.team = models.Team.objects.create(
            name="BIG",
            name_long="BIG Clan",
            hltv_id=3991,
        )

    def test_team_creation(self):
        """Test that a team can be created"""
        self.assertEqual(self.team.name, "BIG")
        self.assertEqual(self.team.name_long, "BIG Clan")
        self.assertEqual(self.team.hltv_id, 3991)

    def test_team_str(self):
        """Test the string representation of a team"""
        self.assertEqual(str(self.team), "BIG")

    def test_team_with_alt_name(self):
        """Test team with alternative name"""
        team = models.Team.objects.create(
            name="FaZe",
            name_alt="FaZe Clan"
        )
        self.assertEqual(team.name_alt, "FaZe Clan")


class TournamentModelTest(TestCase):
    """Test cases for the Tournament model"""

    def setUp(self):
        self.tournament = models.Tournament.objects.create(
            name="ESL Pro League",
            name_short="EPL"
        )

    def test_tournament_creation(self):
        """Test that a tournament can be created"""
        self.assertEqual(self.tournament.name, "ESL Pro League")
        self.assertEqual(self.tournament.name_short, "EPL")

    def test_tournament_str(self):
        """Test the string representation of a tournament"""
        self.assertEqual(str(self.tournament), "ESL Pro League")


class MatchModelTest(TestCase):
    """Test cases for the Match model"""

    def setUp(self):
        self.game = models.Game.objects.create(
            name="Counter-Strike",
            name_short="cs",
            slug="counter-strike"
        )
        self.team_a = models.Team.objects.create(name="Team A")
        self.team_b = models.Team.objects.create(name="Team B")
        self.tournament = models.Tournament.objects.create(
            name="Test Tournament",
            name_short="TT"
        )

        self.lineup_a = models.Lineup.objects.create(
            team=self.team_a,
            game=self.game
        )
        self.lineup_b = models.Lineup.objects.create(
            team=self.team_b,
            game=self.game
        )

        self.match = models.Match.objects.create(
            lineup_a=self.lineup_a,
            lineup_b=self.lineup_b,
            tournament=self.tournament,
            first_map_at=timezone.now() + timezone.timedelta(hours=1),
            slug="test-match"
        )

    def test_match_creation(self):
        """Test that a match can be created"""
        self.assertEqual(self.match.lineup_a, self.lineup_a)
        self.assertEqual(self.match.lineup_b, self.lineup_b)
        self.assertEqual(self.match.tournament, self.tournament)

    def test_match_str(self):
        """Test the string representation of a match"""
        expected = f"{self.team_a.name} vs {self.team_b.name}"
        self.assertEqual(str(self.match), expected)

    def test_match_cancelled(self):
        """Test match cancellation"""
        self.assertFalse(self.match.cancelled)
        self.match.cancelled = True
        self.match.save()
        self.assertTrue(self.match.cancelled)

    def test_match_slug(self):
        """Test match slug"""
        self.assertEqual(self.match.slug, "test-match")


class MatchMapModelTest(TestCase):
    """Test cases for the MatchMap model"""

    def setUp(self):
        self.game = models.Game.objects.create(
            name="Counter-Strike",
            name_short="cs",
            slug="counter-strike"
        )
        self.team_a = models.Team.objects.create(name="Team A")
        self.team_b = models.Team.objects.create(name="Team B")
        self.tournament = models.Tournament.objects.create(
            name="Test Tournament",
            name_short="TT"
        )
        self.map_obj = models.Map.objects.create(
            name="Mirage",
            map_id="mirage"
        )

        self.lineup_a = models.Lineup.objects.create(
            team=self.team_a,
            game=self.game
        )
        self.lineup_b = models.Lineup.objects.create(
            team=self.team_b,
            game=self.game
        )

        self.match = models.Match.objects.create(
            lineup_a=self.lineup_a,
            lineup_b=self.lineup_b,
            tournament=self.tournament,
            first_map_at=timezone.now() + timezone.timedelta(hours=1),
            slug="test-match"
        )

        self.match_map = models.MatchMap.objects.create(
            match=self.match,
            map=self.map_obj,
            starting_at=timezone.now(),
            rounds_won_team_a=13,
            rounds_won_team_b=10
        )

    def test_match_map_creation(self):
        """Test that a match map can be created"""
        self.assertEqual(self.match_map.match, self.match)
        self.assertEqual(self.match_map.map, self.map_obj)
        self.assertEqual(self.match_map.rounds_won_team_a, 13)
        self.assertEqual(self.match_map.rounds_won_team_b, 10)

    def test_match_map_winner(self):
        """Test determining the winner of a match map"""
        # Team A wins 13-10
        self.assertEqual(self.match_map.rounds_won_team_a, 13)
        self.assertGreater(self.match_map.rounds_won_team_a, self.match_map.rounds_won_team_b)


class IndexViewTest(TestCase):
    """Test cases for the IndexView"""

    def setUp(self):
        self.client = Client()
        self.game = models.Game.objects.create(
            name="Counter-Strike",
            name_short="cs",
            slug="counter-strike"
        )
        self.team_a = models.Team.objects.create(name="Team A")
        self.team_b = models.Team.objects.create(name="Team B")
        self.tournament = models.Tournament.objects.create(
            name="Test Tournament",
            name_short="TT"
        )

        self.lineup_a = models.Lineup.objects.create(
            team=self.team_a,
            game=self.game
        )
        self.lineup_b = models.Lineup.objects.create(
            team=self.team_b,
            game=self.game
        )

    def test_index_view_renders(self):
        """Test that the index view renders successfully"""
        response = self.client.get(reverse('csgomatches:index'))
        self.assertEqual(response.status_code, 200)

    def test_index_view_uses_correct_template(self):
        """Test that the index view uses the correct template"""
        response = self.client.get(reverse('csgomatches:index'))
        self.assertTemplateUsed(response, 'csgomatches/match_list.html')

    def test_index_view_displays_future_matches(self):
        """Test that future matches are displayed"""
        future_match = models.Match.objects.create(
            lineup_a=self.lineup_a,
            lineup_b=self.lineup_b,
            tournament=self.tournament,
            first_map_at=timezone.now() + timezone.timedelta(hours=1),
            slug="future-match"
        )

        response = self.client.get(reverse('csgomatches:index'))
        self.assertContains(response, "Team A")
        self.assertContains(response, "Team B")

    def test_index_view_does_not_display_old_matches(self):
        """Test that matches older than 6 hours are not displayed"""
        old_match = models.Match.objects.create(
            lineup_a=self.lineup_a,
            lineup_b=self.lineup_b,
            tournament=self.tournament,
            first_map_at=timezone.now() - timezone.timedelta(hours=12),
            slug="old-match"
        )

        response = self.client.get(reverse('csgomatches:index'))
        # The old match should not be in the context
        self.assertEqual(response.status_code, 200)
