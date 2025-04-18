from django.db import models
from typing import Optional

from django.forms import ValidationError

from csgomatches.models.base_models import BaseWinCondition
from csgomatches.models.global_models import OneOnOneMatchMap, SimpleMatchMap, WinType

class SimpleWinCondition(BaseWinCondition):
    """
    Win condition where a participant can either win or lose, based on a boolean value.
    As the model doesn't have any fields, only one instance of this model can exist.
    """
    class Meta:
        verbose_name = "Simple Win Condition"
        verbose_name_plural = "Simple Win Conditions"
        ordering = ["name"]

    def has_ended(self, match_map: SimpleMatchMap) -> bool:
        return match_map.is_finished

    def get_winner(self, match_map: SimpleMatchMap) -> Optional[WinType]:
        if not self.has_ended(match_map):
            return None
        # match has ended so we can return the participant with higher score
        if match_map.is_won:
            return WinType.WIN
        else:
            return WinType.LOSS

    def clean(self):
        # Ensure that only one instance of this model can exist
        if SimpleWinCondition.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one instance of SimpleWinCondition can exist.", code="multiple_instances")

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = "SimpleWinCondition"
        super().save(*args, **kwargs)


class BestOfWinCondition(BaseWinCondition):
    """
    Win condition for best-of matches with optional overtime.
    A winner is determined based on the scores of the participants.
    The match can end in a draw if {has_draw} is true.
    A game can only be won by a participant if they lead by at least {win_by} points.
    The overtime period will repeat indefinitely until a winner is determined.
    """
    best_of_number = models.PositiveSmallIntegerField(
        default=24,
        blank=True,
        help_text="Best of X, i.e. 24 for CS2 matches",
        verbose_name="Best of X",
    )
    has_overtime = models.BooleanField(
        default=False,
        help_text="Does the match have overtime? False will enable a draw as a result.",
    )
    has_draw = models.BooleanField(
        default=False,
        help_text="Does the match have a draw?",
    )
    best_of_number_overtime = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Best of X for overtime, i.e. 6 for CS2 matches",
        verbose_name="Best of X for overtime",
    )
    win_by = models.PositiveSmallIntegerField(
        default=2,
        help_text="Winning condition: the participant must lead by at least this many points.",
        verbose_name="Win by",
    )

    class Meta:
        verbose_name = "Best of Win Condition"
        verbose_name_plural = "Best of Win Conditions"
        ordering = ["name"]

    def clean(self) -> None:
        """
        Validate the input parameters.
        """
        if self.has_overtime and self.has_draw:
            raise ValidationError("Match cannot have both overtime and draw.", code="overtime_and_draw")
        if self.best_of_number == 0:
            raise ValidationError("Best of number must be greater than 0.", code="best_of_number_zero")
        if self.has_overtime and not self.best_of_number_overtime:
            raise ValidationError("Best of number for overtime must greater than 0 if has_overtime is True.", code="best_of_number_overtime_zero")
        if self.win_by == 0:
            raise ValidationError("Win by must be greater than 0.", code="win_by_zero")
        if self.has_overtime and self.win_by <= 1:
            raise ValidationError("Win by must be greater than 1 if has_overtime is True.", code="win_by_overtime")
        if self.has_draw and self.best_of_number % 2 == 1:
            raise ValidationError("Best of number must be even if has_draw is True.", code="best_of_number_draw")
        super().clean()

    def has_ended(self, match_map: OneOnOneMatchMap) -> bool:
        # Validation should be done in the save method, but we do it here just in case
        # to ensure that the match is in a valid state before checking if it has ended
        BestOfWinCondition._validate(
            self.has_overtime,
            self.has_draw,
            self.best_of_number,
            self.best_of_number_overtime,
            self.win_by
        )

        # Calculate the number of rounds needed to win the match in regulation
        reg_win_at = self.best_of_number // 2 + 1

        p1 = match_map.score_participant_1
        p2 = match_map.score_participant_2

        # Path 1: Game is a draw
        if self.has_draw and p1 == p2 == reg_win_at-1:
            return True

        # Path 2: Game is still with equal scores
        if p1 == p2:
            return False

        score_high, score_low = max(p1, p2), min(p1, p2)

        # Path 3: Game is still in regulation
        if score_high < reg_win_at:
            return False

        # Path 4: Game has ended in regulation
        if score_high == reg_win_at and score_low <= reg_win_at - self.win_by:
            return True

        # Path 5: There is no overtime, so the game is in 'extra time', until a team wins by win_by points
        if not self.has_overtime:
            return score_high - score_low >= self.win_by

        # At this point, we know that the game is in overtime or has ended in overtime
        # Path 5: Game is in overtime
        # At this point best_of_number_overtime shouldn't be None, but we check it just in case
        if self.best_of_number_overtime is None:
            raise ValueError("Match is in overtime, but best_of_number_overtime is None."
                                f" best_of_number: {self.best_of_number}, has_overtime: {self.has_overtime}, "
                                f"has_draw: {self.has_draw}, best_of_number_overtime: {self.best_of_number_overtime}, "
                                f"score_participant_1: {self.score_participant_1}, score_participant_2: {self.score_participant_2}, "
                                f"win_by: {self.win_by}")

        # Calculate total overtime score
        total_overtime_score_high = score_high - (reg_win_at - 1)
        total_overtime_score_low = score_low - (reg_win_at - 1)

        overtime_win_at = self.best_of_number_overtime // 2 + 1

        # As overtimes repeat indefinitely, we can calculate the current iteration of the overtime
        current_overtime = total_overtime_score_low // (overtime_win_at-1)

        # Calculate the score of the current overtime
        current_overtime_score_high = total_overtime_score_high - current_overtime * (overtime_win_at-1)
        current_overtime_score_low = total_overtime_score_low - current_overtime * (overtime_win_at-1)

        # Path 6: Game has ended in overtime
        if current_overtime_score_high == overtime_win_at and current_overtime_score_low <= overtime_win_at - self.win_by:
            return True

        # Path 7: Game is still in overtime
        else:
            return False

    def get_winner(self, match_map: OneOnOneMatchMap) -> Optional[WinType]:
        if not self.has_ended(match_map):
            return None
        # match has ended so we can return the participant with higher score
        if match_map.score_participant_1 > match_map.score_participant_2:
            return WinType.PARTICIPANT_1
        elif match_map.score_participant_1 < match_map.score_participant_2:
            return WinType.PARTICIPANT_2
        else:
            return WinType.DRAW


    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"BO{self.best_of_number}{f'OT_BO{self.best_of_number_overtime}' if self.has_overtime else ''}{'DRAW_POSSIBLE' if self.has_draw else ''}_WIN_BY{self.win_by}"
        super().save(*args, **kwargs)
