import unittest

from csgomatches.check_best_of_win import has_ended

class TestBestOfWinCondition(unittest.TestCase):
    # Input Parameters:
    # best_of_number
    # has_overtime
    # has_draw
    # best_of_number_overtime
    # score_participant_1
    # score_participant_2
    # win_by

    def test_validation(self):
        # overtime and draw are mutually exclusive
        with self.assertRaises(ValueError):
            has_ended(24, True, True, 6, 12, 12, 2)
        # best_of_number can't be 0
        with self.assertRaises(ValueError):
            has_ended(0, False, False, 6, 12, 12, 2)
        # win_by can't be 0
        with self.assertRaises(ValueError):
            has_ended(24, False, False, 6, 12, 12, 0)
        # best_of_number_overtime can't be None if has_overtime is True
        with self.assertRaises(ValueError):
            has_ended(24, True, False, None, 12, 12, 2)
        # best_of_number_overtime can't be 0 if has_overtime is True
        with self.assertRaises(ValueError):
            has_ended(24, True, False, 0, 12, 12, 2)
        # win_by can't be 1 if has_overtime is True
        with self.assertRaises(ValueError):
            has_ended(24, True, False, 6, 12, 12, 1)
        # best_of_number can't be odd if has_draw is True
        with self.assertRaises(ValueError):
            has_ended(25, False, True, 6, 12, 12, 2)

    def test_draw(self):
        # Draw case
        self.assertTrue(has_ended(24, False, True, 6, 12, 12, 2))
        self.assertTrue(has_ended(22, False, True, 6, 11, 11, 2))
        self.assertTrue(has_ended(24, False, True, 6, 12, 12, 3))
        # Not a draw case
        self.assertFalse(has_ended(24, False, True, 6, 12, 11, 2))
        self.assertFalse(has_ended(24, False, True, 6, 12, 10, 2))
        self.assertFalse(has_ended(24, False, False, 6, 12, 12, 2))

    def test_ot(self):
        # Game is still in regulation
        self.assertFalse(has_ended(24, True, False, 6, 12, 11, 2))
        self.assertFalse(has_ended(24, True, False, 6, 12, 10, 2))
        self.assertFalse(has_ended(24, True, False, 6, 4, 12, 2))
        # Game has ended in regulation
        self.assertTrue(has_ended(24, True, False, 6, 11, 13, 2))
        self.assertTrue(has_ended(24, True, False, 6, 13, 4, 2))
        # Game is in overtime
        self.assertFalse(has_ended(24, True, False, 6, 12, 12, 2))
        self.assertFalse(has_ended(24, True, False, 6, 12, 13, 2))
        self.assertFalse(has_ended(24, True, False, 6, 13, 12, 2))
        self.assertFalse(has_ended(24, True, False, 6, 12, 14, 2))
        self.assertFalse(has_ended(24, True, False, 6, 15, 15, 2))
        self.assertFalse(has_ended(24, True, False, 6, 15, 16, 2))
        self.assertFalse(has_ended(24, True, False, 6, 17, 16, 2))
        # Game has ended in overtime
        self.assertTrue(has_ended(24, True, False, 6, 16, 12, 2))
        self.assertTrue(has_ended(24, True, False, 6, 16, 13, 2))
        self.assertTrue(has_ended(24, True, False, 6, 16, 14, 2))
        self.assertTrue(has_ended(24, True, False, 6, 12, 16, 2))
        self.assertTrue(has_ended(24, True, False, 6, 13, 16, 2))
        self.assertTrue(has_ended(24, True, False, 6, 14, 16, 2))
        self.assertTrue(has_ended(24, True, False, 6, 15, 19, 2))
        self.assertTrue(has_ended(24, True, False, 6, 16, 19, 2))
        self.assertTrue(has_ended(24, True, False, 6, 17, 19, 2))
        self.assertTrue(has_ended(24, True, False, 6, 19, 15, 2))
        self.assertTrue(has_ended(24, True, False, 6, 19, 16, 2))
        self.assertTrue(has_ended(24, True, False, 6, 19, 17, 2))

    def test_no_ot_no_draw(self):
        # Game is still ongoing
        self.assertFalse(has_ended(24, False, False, 6, 11, 12, 2))
        self.assertFalse(has_ended(24, False, False, 6, 12, 11, 2))
        self.assertFalse(has_ended(24, False, False, 6, 12, 12, 2))
        self.assertFalse(has_ended(24, False, False, 6, 12, 10, 2))
        self.assertFalse(has_ended(24, False, False, 6, 12, 13, 2))
        # Game has ended
        self.assertTrue(has_ended(24, False, False, 6, 13, 11, 2))
        self.assertTrue(has_ended(24, False, False, 6, 12, 14, 2))
        self.assertTrue(has_ended(24, False, False, 6, 11, 13, 2))

if __name__ == "__main__":
    unittest.main()
