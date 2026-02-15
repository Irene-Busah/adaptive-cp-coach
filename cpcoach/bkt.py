from __future__ import annotations


def bkt_update(
        p_mastery: float,
        correct: bool,
        p_slip: float=0.10,
        p_guess: float=0.20,
        p_learn: float=0.15
) -> float:
    """
    Bayesian Knowledge Tracing update for ONE skill after ONE attempt.
    
    :param p_mastery: Current probability that the student has mastered the skill
                  before observing the latest attempt. Must be between 0 and 1.
    :type p_mastery: float
    :param correct: Whether the student answered the problem correctly (True for AC,
                False for incorrect verdict such as WA/TLE/RE)
    :type correct: bool
    :param p_slip: Probability of making a mistake despite knowing the skill
    :type p_slip: float
    :param p_guess: Probability of answering correctly despite not knowing the skill
    :type p_guess: float
    :param p_learn: Probability of learning (transitioning from not knowing to knowing)
                the skill after this attempt
    :type p_learn: float
    :return: Updated probability that the student has mastered the skill
         after incorporating the observation and learning transition
    :rtype: float
    """

    p = max(0.0, min(1.0, p_mastery))

    if correct:
        num = p * (1.0 - p_slip)
        den = num + (1.0 - p) * p_guess
        p_given = num / den if den > 0 else p
    else:
        num = p * p_slip
        den = num + (1.0 - p) * (1.0 - p_guess)
        p_given = num / den if den > 0 else p
    
    # learning transition
    p_next = p_given + (1.0 - p_given) * p_learn
    return max(0.0, min(1.0, p_next))




