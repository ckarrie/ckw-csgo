from django.test import TestCase
from unittest.mock import Mock

from csgomatches.models.win_conditions import BestOfWinCondition

class TestBestOfWinCondition(TestCase):
    @classmethod
    def setUpClass(cls):
        # WinCondition for CS2 matches
        BestOfWinCondition.objects.create(
            best_of_number=24,
            has_overtime=True,
            has_draw=False,
            best_of_number_overtime=6,
            win_by=2
        )
        # Generic BO7 WinCondition
        BestOfWinCondition.objects.create(
            best_of_number=7,
            has_overtime=False,
            has_draw=False,
            best_of_number_overtime=None,
            win_by=1
        )
        # WinCondition without overtime and draw, but requires win_by 2
        BestOfWinCondition.objects.create(
            best_of_number=7,
            has_overtime=False,
            has_draw=False,
            best_of_number_overtime=None,
            win_by=2
        )
        # WinCondition for CS2 matches with draw
        BestOfWinCondition.objects.create(
            best_of_number=24,
            has_overtime=False,
            has_draw=True,
            best_of_number_overtime=None,
            win_by=2
        )
        cls.cs2_win_condition = BestOfWinCondition.objects.get(
            best_of_number=24,
            has_overtime=True,
            has_draw=False,
            best_of_number_overtime=6,
            win_by=2
        )
        cls.generic_bo7_win_condition = BestOfWinCondition.objects.get(
            best_of_number=7,
            has_overtime=False,
            has_draw=False,
            best_of_number_overtime=None,
            win_by=1
        )
        cls.no_draw_no_ot_win_condition = BestOfWinCondition.objects.get(
            best_of_number=7,
            has_overtime=False,
            has_draw=False,
            best_of_number_overtime=None,
            win_by=2
        )
        cls.cs2_draw_win_condition = BestOfWinCondition.objects.get(
            best_of_number=24,
            has_overtime=False,
            has_draw=True,
            best_of_number_overtime=None,
            win_by=2
        )
        super().setUpClass()

    def test_has_ended_validation(self):
        # overtime and draw are mutually exclusive
        with self.assertRaises(ValueError):
            BestOfWinCondition.objects.create(
                best_of_number=24,
                has_overtime=True,
                has_draw=True,
                best_of_number_overtime=6,
                win_by=2
            )
        # best_of_number can't be 0
        with self.assertRaises(ValueError):
            BestOfWinCondition.objects.create(
                best_of_number=0,
                has_overtime=False,
                has_draw=False,
                best_of_number_overtime=6,
                win_by=2
            )
        # win_by can't be 0
        with self.assertRaises(ValueError):
            BestOfWinCondition.objects.create(
                best_of_number=24,
                has_overtime=False,
                has_draw=False,
                best_of_number_overtime=6,
                win_by=0
            )
        # best_of_number_overtime can't be None if has_overtime is True
        with self.assertRaises(ValueError):
            BestOfWinCondition.objects.create(
                best_of_number=24,
                has_overtime=True,
                has_draw=False,
                best_of_number_overtime=None,
                win_by=2
            )
        # best_of_number_overtime can't be 0 if has_overtime is True
        with self.assertRaises(ValueError):
            BestOfWinCondition.objects.create(
                best_of_number=24,
                has_overtime=True,
                has_draw=False,
                best_of_number_overtime=0,
                win_by=2
            )
        # win_by can't be 1 if has_overtime is True
        with self.assertRaises(ValueError):
            BestOfWinCondition.objects.create(
                best_of_number=24,
                has_overtime=True,
                has_draw=False,
                best_of_number_overtime=6,
                win_by=1
            )
        # best_of_number can't be odd if has_draw is True
        with self.assertRaises(ValueError):
            BestOfWinCondition.objects.create(
                best_of_number=25,
                has_overtime=False,
                has_draw=True,
                best_of_number_overtime=None,
                win_by=2
            )

    def test_has_ended_draw(self):
        # Draw case
        self.assertTrue(TestBestOfWinCondition.cs2_draw_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=12)))
        # Not a draw case
        self.assertFalse(TestBestOfWinCondition.generic_bo7_win_condition.has_ended
                        (match_map=Mock(score_participant_1=3, score_participant_2=3)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=11)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=10)))
        self.assertFalse(TestBestOfWinCondition.no_draw_no_ot_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=12)))

    def test_has_ended_ot(self):
        # Game is still in regulation
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=11)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=10)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=4, score_participant_2=12)))
        # Game has ended in regulation
        self.assertTrue(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=11, score_participant_2=13)))
        self.assertTrue(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=13, score_participant_2=4)))
        # Game is in overtime
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=12)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=13)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=13, score_participant_2=12)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=12, score_participant_2=14)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=15, score_participant_2=15)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=15, score_participant_2=16)))
        self.assertFalse(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=17, score_participant_2=16)))
        # Game has ended in overtime
        self.assertTrue(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=16, score_participant_2=12)))
        self.assertTrue(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=16, score_participant_2=13)))
        self.assertTrue(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=16, score_participant_2=14)))
        self.assertTrue(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=14, score_participant_2=16)))
        self.assertTrue(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=15, score_participant_2=19)))
        self.assertTrue(TestBestOfWinCondition.cs2_win_condition.has_ended
                        (match_map=Mock(score_participant_1=19, score_participant_2=16)))

    def test_has_ended_no_ot_no_draw(self):
        # Game is still ongoing
        self.assertFalse(TestBestOfWinCondition.no_draw_no_ot_win_condition.has_ended
                        (match_map=Mock(score_participant_1=1, score_participant_2=3)))
        self.assertFalse(TestBestOfWinCondition.no_draw_no_ot_win_condition.has_ended
                        (match_map=Mock(score_participant_1=3, score_participant_2=3)))
        self.assertFalse(TestBestOfWinCondition.no_draw_no_ot_win_condition.has_ended
                        (match_map=Mock(score_participant_1=3, score_participant_2=4)))
        self.assertFalse(TestBestOfWinCondition.no_draw_no_ot_win_condition.has_ended
                        (match_map=Mock(score_participant_1=5, score_participant_2=4)))
        # Game has ended
        self.assertTrue(TestBestOfWinCondition.no_draw_no_ot_win_condition.has_ended
                        (match_map=Mock(score_participant_1=3, score_participant_2=5)))
        self.assertTrue(TestBestOfWinCondition.no_draw_no_ot_win_condition.has_ended
                        (match_map=Mock(score_participant_1=4, score_participant_2=6)))
        self.assertTrue(TestBestOfWinCondition.no_draw_no_ot_win_condition.has_ended
                        (match_map=Mock(score_participant_1=6, score_participant_2=4)))
