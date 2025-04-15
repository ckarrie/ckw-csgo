from typing import Optional


def has_ended(
        best_of_number: int,
        has_overtime: bool,
        has_draw: bool,
        best_of_number_overtime: Optional[int],
        score_participant_1: int,
        score_participant_2: int,
        win_by: int) -> bool:
    """
    Check if the match has ended based on the scores and win conditions.
    """
    # win_by and all best of numbers are not negative, which is enforded in the model
    # so we don't need to check this

    # invalid inputs
    if has_overtime and has_draw:
        raise ValueError("Match cannot have both overtime and draw.")
    if best_of_number == 0:
        raise ValueError("Best of number must be greater than 0.")
    if has_overtime and not best_of_number_overtime:
        raise ValueError("Best of number for overtime must greater than 0 if has_overtime is True.")
    if win_by == 0:
        raise ValueError("Win by must be greater than 0.")
    if has_overtime and win_by <= 1:
        raise ValueError("Win by must be greater than 1 if has_overtime is True.")
    if has_draw and best_of_number % 2 == 1:
        raise ValueError("Best of number must be even if has_draw is True.")

    # Calculate the number of rounds needed to win the match in regulation
    reg_win_at = best_of_number // 2 + 1

    # Path 1: Game is a draw
    if has_draw and score_participant_1 == score_participant_2 == reg_win_at-1:
        return True

    # Path 2: Game is still with equal scores
    if score_participant_1 == score_participant_2:
        return False

    score_high, score_low = max(score_participant_1, score_participant_2), min(score_participant_1, score_participant_2)

    # Path 3: Game is still in regulation
    if score_high < reg_win_at:
        return False

    # Path 4: Game has ended in regulation
    if score_high == reg_win_at and score_low <= reg_win_at - win_by:
        return True

    # Path 5: There is no overtime, so the game is in 'extra time', until a team wins by win_by points
    if not has_overtime:
        return score_high - score_low >= win_by

    # At this point, we know that the game is in overtime or has ended in overtime
    # Path 5: Game is in overtime
    # At this point best_of_number_overtime shouldn't be None, but we check it just in case
    if best_of_number_overtime is None:
        raise ValueError("Match is in overtime, but best_of_number_overtime is None."
                            f" best_of_number: {best_of_number}, has_overtime: {has_overtime}, "
                            f"has_draw: {has_draw}, best_of_number_overtime: {best_of_number_overtime}, "
                            f"score_participant_1: {score_participant_1}, score_participant_2: {score_participant_2}, "
                            f"win_by: {win_by}")

    # Calculate total overtime score
    total_overtime_score_high = score_high - (reg_win_at - 1)
    total_overtime_score_low = score_low - (reg_win_at - 1)

    overtime_win_at = best_of_number_overtime // 2 + 1

    # As overtimes repeat indefinitely, we can calculate the current iteration of the overtime
    current_overtime = total_overtime_score_low // (overtime_win_at-1)

    # Calculate the score of the current overtime
    current_overtime_score_high = total_overtime_score_high - current_overtime * (overtime_win_at-1)
    current_overtime_score_low = total_overtime_score_low - current_overtime * (overtime_win_at-1)

    # Path 6: Game has ended in overtime
    if current_overtime_score_high == overtime_win_at and current_overtime_score_low <= overtime_win_at - win_by:
        return True

    # Path 7: Game is still in overtime
    else:
        return False
