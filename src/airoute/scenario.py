"""All inputs of the scenario, in one place, clearly labelled as hypothetical.

The project guidelines for this Final Project state that "predefined
probabilities, transition tables, rewards and toy maps are allowed" and that
assumptions must be clearly labelled. Every number used anywhere in the
package is defined here so that a reader can check the whole model at once.

Scenario
--------
A resident of Astana lives near the river embankment (cell ``S``) and has to
reach the university (cell ``G``) on a winter evening. In the coal-heating
season a temperature inversion can trap particulates near the ground, so
concentrations differ from block to block and the resident faces two questions:

    * should I leave now, or wait one more hour indoors?
    * if I leave now, which route exposes me to the least smoke?

The adviser answers both with three (plus one bonus) course algorithms.
"""

from fractions import Fraction

# ---------------------------------------------------------------------------
# Hidden states of the air
# ---------------------------------------------------------------------------
#: "A" = acceptable air, "H" = hazardous air. Two states, as the guidelines ask.
STATES = ("A", "H")
STATE_NAMES = {
    "A": "Acceptable (PM2.5 <= 50 ug/m3)",
    "H": "Hazardous (PM2.5 > 100 ug/m3)",
}

#: Actions of the MDP. Two actions, as the guidelines ask.
ACTIONS = ("Go", "Wait")
ACTION_NAMES = {
    "Go": "leave now and walk for one hour",
    "Wait": "stay one more hour indoors with the air purifier on",
}

# ---------------------------------------------------------------------------
# Part 1 - Bayesian inference: the home PM2.5 sensor
# ---------------------------------------------------------------------------
# Exact fractions keep the printed arithmetic identical to the hand calculation.
PRIOR_HAZARDOUS = Fraction(3, 10)        # P(H) before any reading
SENSOR_SENSITIVITY = Fraction(17, 20)    # P(alarm | H), true positive rate
SENSOR_FALSE_ALARM = Fraction(1, 5)      # P(alarm | A), false positive rate

#: The single observation of the base scenario: the cheap sensor shouts "alarm".
OBSERVATION = "alarm"
SENSOR_SIGNALS = ("alarm", "calm")

# ---------------------------------------------------------------------------
# Part 2 - MDP: transitions and rewards
# ---------------------------------------------------------------------------
# P(next state | current state). The atmosphere evolves hour by hour.
# Assumption: staying indoors with a purifier does not change the outdoor air,
# so the transition matrix is the same for both actions. What differs is the
# immediate reward.
TRANSITIONS = {
    "A": {"A": Fraction(7, 10), "H": Fraction(3, 10)},
    "H": {"A": Fraction(2, 5), "H": Fraction(3, 5)},
}

DISCOUNT = Fraction(9, 10)   # gamma = 0.9, one hour per step

# Waiting is modelled as a fixed cost, independent of the state:
#   * you lose one hour of the day,
#   * but in hazardous air you also avoid the exposure, which is why "Wait"
#     in state H is much cheaper than "Go" in state H.
REWARD_WAIT = {"A": Fraction(-4), "H": Fraction(-6)}

#: Benefit of arriving, in utility points, before any exposure cost.
ARRIVAL_BENEFIT = Fraction(12)

#: Health cost per unit of inhaled dose, in utility points.
DOSE_COST = Fraction(1, 50)   # 0.02

#: Average PM2.5 concentration (ug/m3) per unit of block weight, by state.
CONCENTRATION = {"A": Fraction(15), "H": Fraction(75)}

# ---------------------------------------------------------------------------
# Part 3 - A* search: the 6x6 map of city blocks
# ---------------------------------------------------------------------------
# Each passable cell carries a relative PM2.5 weight:
#   1 = park or quiet courtyard, 2 = quiet residential,
#   3-4 = ordinary street, 5 = busy avenue.
# None = impassable (fenced railway depot, closed courtyards, a walled site).
GRID = [
    [1,    1,    1,    1,    1,    1],      # row 0: park belt along the Yesil embankment
    [1,    None, None, 4,    4,    4],      # row 1
    [1,    None, None, 4,    5,    4],      # row 2
    [1,    1,    1,    4,    5,    4],      # row 3: Mangilik Yel avenue, heavy traffic
    [None, None, 1,    4,    5,    4],      # row 4
    [None, None, 2,    4,    4,    4],      # row 5: residential side, home at (5, 2)
]

ROWS = len(GRID)
COLS = len(GRID[0])

START = (5, 2)   # S, home
GOAL = (0, 5)    # G, university

#: Smallest possible cell weight; used to build the admissible A* heuristic.
MIN_CELL_WEIGHT = min(w for row in GRID for w in row if w is not None)

#: Movement is allowed to the four orthogonal neighbours.
NEIGHBOUR_ORDER = ((-1, 0), (0, 1), (1, 0), (0, -1))   # up, right, down, left

# ---------------------------------------------------------------------------
# Part 4 (bonus) - HMM: three hourly sensor readings
# ---------------------------------------------------------------------------
INITIAL_DISTRIBUTION = {"A": Fraction(7, 10), "H": Fraction(3, 10)}

# The emission model is the same sensor as in Part 1, which is what makes the
# two parts consistent: P(alarm | H) = 0.85 and P(alarm | A) = 0.20.
EMISSIONS = {
    "A": {"alarm": SENSOR_FALSE_ALARM, "calm": 1 - SENSOR_FALSE_ALARM},
    "H": {"alarm": SENSOR_SENSITIVITY, "calm": 1 - SENSOR_SENSITIVITY},
}

#: Three consecutive hourly readings: two alarms, then the air clears.
OBSERVATION_SEQUENCE = ("alarm", "alarm", "calm")


def dose(state, route_weight):
    """Inhaled dose for walking a route of total block weight ``route_weight``.

    dose = concentration(state) * sum of block weights along the route.
    The unit is arbitrary "dose units"; only ratios of doses matter here.
    """
    return CONCENTRATION[state] * Fraction(route_weight)


def reward_go(state, route_weight):
    """Immediate reward of action "Go" in ``state`` when the route costs
    ``route_weight`` block-weight units.

    R(s, Go) = arrival benefit - health cost per dose * dose(s, route)

    This is the single place where the search result enters the decision
    model: a cleaner route lowers the dose and therefore raises R(s, Go).
    """
    return ARRIVAL_BENEFIT - DOSE_COST * dose(state, route_weight)


SCENARIO = {
    "states": STATES,
    "actions": ACTIONS,
    "prior_hazardous": PRIOR_HAZARDOUS,
    "sensor_sensitivity": SENSOR_SENSITIVITY,
    "sensor_false_alarm": SENSOR_FALSE_ALARM,
    "observation": OBSERVATION,
    "transitions": TRANSITIONS,
    "discount": DISCOUNT,
    "reward_wait": REWARD_WAIT,
    "grid": GRID,
    "start": START,
    "goal": GOAL,
    "observation_sequence": OBSERVATION_SEQUENCE,
}
