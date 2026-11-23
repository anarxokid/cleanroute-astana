"""Tests for CleanRoute Astana.

The project checklist requires at least one working test case; this suite
checks every number that the report and the presentation quote, so a change
in the scenario cannot silently invalidate the written deliverables.

Run either way::

    python -m pytest tests -q          # with pytest installed
    python tests/test_airoute.py       # with the standard library only
"""

import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from airoute import bayes, hmm, mdp, pipeline, search
from airoute.scenario import GOAL, GRID, START, reward_go

TOL = 1e-9


# ---------------------------------------------------------------------------
# Part 1 - Bayesian inference
# ---------------------------------------------------------------------------
def test_bayes_posterior_is_exact_fraction():
    result = bayes.update("alarm")
    assert result.posterior_hazardous == Fraction(51, 79)
    assert result.posterior_acceptable == Fraction(28, 79)


def test_bayes_posteriors_sum_to_one():
    for signal in ("alarm", "calm"):
        result = bayes.update(signal)
        assert result.posterior_hazardous + result.posterior_acceptable == 1


def test_bayes_calm_lowers_the_prior():
    result = bayes.update("calm")
    assert result.posterior_hazardous == Fraction(9, 121)
    assert result.posterior_hazardous < result.prior_hazardous


def test_bayes_likelihood_ratio():
    result = bayes.update("alarm")
    assert result.likelihood_ratio == Fraction(17, 4)


def test_bayes_rejects_unknown_signal():
    try:
        bayes.update("smoke")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown sensor signal must raise ValueError")


# ---------------------------------------------------------------------------
# Part 2 - search
# ---------------------------------------------------------------------------
def _assert_valid_route(route):
    assert route[0] == START and route[-1] == GOAL
    for previous, current in zip(route, route[1:]):
        assert abs(previous[0] - current[0]) + abs(previous[1] - current[1]) == 1
        assert GRID[current[0]][current[1]] is not None


def test_bfs_finds_the_shortest_route():
    result = search.bfs()
    _assert_valid_route(result.route)
    assert result.steps == 8
    assert result.weight == 19


def test_astar_and_ucs_agree_on_the_optimum():
    astar = search.astar()
    ucs = search.ucs()
    _assert_valid_route(astar.route)
    _assert_valid_route(ucs.route)
    assert astar.weight == ucs.weight == 14
    assert astar.steps == ucs.steps == 12


def test_astar_expands_no_more_nodes_than_ucs():
    assert search.astar().expanded < search.ucs().expanded


def test_astar_beats_bfs_on_dose():
    assert search.astar().weight < search.bfs().weight


def test_route_weight_matches_the_map():
    for result in (search.bfs(), search.astar()):
        assert result.weight == sum(GRID[r][c] for r, c in result.route)


def test_heuristic_is_admissible():
    # h never overestimates: the remaining cost from the start is the optimal
    # route weight minus the start cell, and h(start) must not exceed it.
    optimal = search.astar().weight - GRID[START[0]][START[1]]
    assert search.heuristic(START) <= optimal
    assert search.heuristic(GOAL) == 0


# ---------------------------------------------------------------------------
# Part 3 - MDP
# ---------------------------------------------------------------------------
def test_reward_model_is_exact():
    assert reward_go("A", 14) == Fraction(39, 5)      # 12 - 0.02 * 15 * 14
    assert reward_go("H", 14) == Fraction(-9)          # 12 - 0.02 * 75 * 14
    assert reward_go("A", 19) == Fraction(63, 10)
    assert reward_go("H", 19) == Fraction(-33, 2)


def test_decision_thresholds_are_exact():
    belief = bayes.update("alarm").belief
    baseline = mdp.decide(belief, 19)
    optimal = mdp.decide(belief, 14)
    assert baseline.threshold == Fraction(103, 208)
    assert optimal.threshold == Fraction(59, 74)


def test_route_planning_flips_the_decision():
    belief = bayes.update("alarm").belief
    assert mdp.decide(belief, 19).action == "Wait"
    assert mdp.decide(belief, 14).action == "Go"


def test_q_values_match_hand_calculation():
    belief = bayes.update("alarm").belief
    decision = mdp.decide(belief, 14)
    expected_go = Fraction(28, 79) * Fraction(39, 5) + Fraction(51, 79) * Fraction(-9)
    assert abs(float(decision.q_values["Go"]) - float(expected_go)) < TOL


def test_value_iteration_converges_to_the_expected_fixed_point():
    policy = mdp.value_iteration(14)
    assert policy.values["A"] == Fraction(39, 5)
    assert abs(float(policy.values["H"]) - (-798 / 115)) < 1e-6
    assert policy.policy == {"A": "Go", "H": "Wait"}


def test_value_iteration_values_satisfy_the_bellman_equation():
    from airoute.scenario import DISCOUNT, REWARD_WAIT, TRANSITIONS

    policy = mdp.value_iteration(14)
    rewards = mdp.reward_table(14)
    for state in ("A", "H"):
        go = rewards[state]["Go"]
        wait = REWARD_WAIT[state] + DISCOUNT * sum(
            TRANSITIONS[state][nxt] * policy.values[nxt] for nxt in ("A", "H")
        )
        assert abs(float(policy.values[state]) - float(max(go, wait))) < 1e-6


def test_three_readings_make_go_safe_for_both_routes():
    belief = hmm.forward(("alarm", "alarm", "calm")).final_belief
    assert mdp.decide(belief, 19).action == "Go"
    assert mdp.decide(belief, 14).action == "Go"


# ---------------------------------------------------------------------------
# Part 4 - HMM
# ---------------------------------------------------------------------------
def test_viterbi_decodes_the_expected_sequence():
    result = hmm.viterbi(("alarm", "alarm", "calm"))
    assert result.sequence == ["H", "H", "A"]


def test_forward_first_step_equals_the_bayes_posterior():
    # The HMM reuses the Part 1 sensor model, so after one reading both must
    # give exactly the same belief.
    belief = hmm.forward(("alarm",)).final_belief
    assert belief["H"] == bayes.update("alarm").posterior_hazardous


def test_forward_beliefs_are_normalised():
    result = hmm.forward(("alarm", "alarm", "calm"))
    for belief in result.beliefs:
        assert belief["A"] + belief["H"] == 1


def test_forward_belief_falls_after_the_calm_reading():
    beliefs = hmm.forward(("alarm", "alarm", "calm")).beliefs
    assert float(beliefs[1]["H"]) > float(beliefs[0]["H"])
    assert float(beliefs[2]["H"]) < float(beliefs[0]["H"])
    assert abs(float(beliefs[2]["H"]) - 0.181406) < 1e-5


def test_hmm_rejects_unknown_signal():
    try:
        hmm.viterbi(("alarm", "fog"))
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown sensor signal must raise ValueError")


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------
def test_pipeline_recommendation():
    result = pipeline.run()
    assert result.recommendation["action"] == "Go"
    assert result.recommendation["route"] == search.astar().route
    assert result.recommendation["route_weight"] == 14


def test_pipeline_dose_reduction():
    result = pipeline.run()
    saving, percent = result.dose_reduction
    assert saving == 5
    assert abs(percent - 26.31578947368421) < 1e-6


def test_pipeline_belief_ordering_tells_the_story():
    result = pipeline.run()
    single = float(result.bayes_alarm.posterior_hazardous)
    after_two = float(result.forward.beliefs[1]["H"])
    after_three = float(result.forward.beliefs[2]["H"])
    assert after_two > single > after_three


if __name__ == "__main__":
    failures = 0
    for name, function in sorted(globals().items()):
        if name.startswith("test_") and callable(function):
            try:
                function()
                print(f"  PASS  {name}")
            except AssertionError as error:
                failures += 1
                print(f"  FAIL  {name}: {error}")
    print()
    total = sum(1 for name in globals() if name.startswith("test_"))
    print(f"{total - failures} passed, {failures} failed")
    sys.exit(1 if failures else 0)
