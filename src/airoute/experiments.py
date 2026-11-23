"""Experiments: how sensitive is the recommendation to the assumptions?

The scenario numbers are hypothetical, so the honest question is not "is the
answer right" but "which assumptions actually change the answer". Two sweeps
answer that:

``sweep_prior``
    Vary the prior P(H) over the whole 0.05-0.95 range. For each value, update
    with one 'alarm' reading and decide under both routes. The priors where the
    two routes disagree are exactly the region where route planning matters.

``sweep_sensor``
    Vary the sensor false-alarm rate from 0.05 to 0.50 with the prior fixed.
    This shows how much a better (or worse) sensor changes the belief and,
    through it, the recommendation.

Both sweeps are deterministic and use only the algorithms of the package, so
every number in the resulting table is reproducible by re-running the module.
"""

import csv
import os
from dataclasses import dataclass, field
from fractions import Fraction

from airoute import bayes, mdp

RESULTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results",
)


@dataclass
class SweepRow:
    parameter: float
    posterior_h: Fraction
    decision_shortest: str
    decision_astar: str
    threshold_shortest: Fraction
    threshold_astar: Fraction


@dataclass
class Sweep:
    name: str
    parameter_name: str
    rows: list = field(default_factory=list)

    @property
    def disagreements(self):
        return [row for row in self.rows
                if row.decision_shortest != row.decision_astar]


def _decide(posterior_h, weight_shortest, weight_astar):
    belief = {"H": posterior_h, "A": 1 - posterior_h}
    short = mdp.decide(belief, weight_shortest)
    astar = mdp.decide(belief, weight_astar)
    return short, astar


def sweep_prior(weight_shortest, weight_astar, values=None):
    values = values or [Fraction(k, 100) for k in range(5, 100, 5)]
    sweep = Sweep(name="prior sweep", parameter_name="prior P(H)")
    for prior in values:
        result = bayes.update("alarm", prior_hazardous=prior)
        short, astar = _decide(result.posterior_hazardous, weight_shortest, weight_astar)
        sweep.rows.append(SweepRow(
            parameter=float(prior),
            posterior_h=result.posterior_hazardous,
            decision_shortest=short.action,
            decision_astar=astar.action,
            threshold_shortest=short.threshold,
            threshold_astar=astar.threshold,
        ))
    return sweep


def sweep_sensor(weight_shortest, weight_astar, values=None):
    values = values or [Fraction(k, 100) for k in range(5, 55, 5)]
    sweep = Sweep(name="sensor sweep", parameter_name="false-alarm rate P(alarm|A)")
    for false_alarm in values:
        result = bayes.update("alarm", false_alarm=false_alarm)
        short, astar = _decide(result.posterior_hazardous, weight_shortest, weight_astar)
        sweep.rows.append(SweepRow(
            parameter=float(false_alarm),
            posterior_h=result.posterior_hazardous,
            decision_shortest=short.action,
            decision_astar=astar.action,
            threshold_shortest=short.threshold,
            threshold_astar=astar.threshold,
        ))
    return sweep


def summarise(sweep):
    """One paragraph of plain-language interpretation of a sweep."""
    disagree = sweep.disagreements
    if not disagree:
        return (
            f"In the {sweep.name} the two routes always recommend the same action, "
            f"so route planning does not change the decision anywhere in the swept range."
        )
    lo = min(row.parameter for row in disagree)
    hi = max(row.parameter for row in disagree)
    return (
        f"In the {sweep.name} the shortest-distance route and the A* route disagree for "
        f"{len(disagree)} of {len(sweep.rows)} values of {sweep.parameter_name} "
        f"(from {lo:.2f} to {hi:.2f}): there the shortest route says "
        f"'{disagree[0].decision_shortest}' while the minimum-exposure route says "
        f"'{disagree[0].decision_astar}'. Outside that band both routes agree, so the "
        f"recommendation is robust to the assumption."
    )


def run(weight_shortest=19, weight_astar=14):
    """Both sweeps, ready to be printed or plotted."""
    prior = sweep_prior(weight_shortest, weight_astar)
    sensor = sweep_sensor(weight_shortest, weight_astar)
    return prior, sensor


def write_csv(sweep, filename):
    """Save one sweep as a CSV artifact so the numbers can be re-checked."""
    path = os.path.join(RESULTS, filename)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([sweep.parameter_name, "P(H|alarm)",
                         "decision_shortest", "decision_astar", "agree"])
        for row in sweep.rows:
            writer.writerow([
                f"{row.parameter:.2f}",
                f"{float(row.posterior_h):.4f}",
                row.decision_shortest,
                row.decision_astar,
                int(row.decision_shortest == row.decision_astar),
            ])
    return path


if __name__ == "__main__":
    from airoute import render, search

    bfs = search.bfs()
    astar = search.astar()
    prior_sweep, sensor_sweep = run(bfs.weight, astar.weight)

    for sweep in (prior_sweep, sensor_sweep):
        render.section("E", f"EXPERIMENT - {sweep.name.upper()}")
        print(f"  swept parameter: {sweep.parameter_name}")
        render.table(
            [sweep.parameter_name, "P(H | alarm)", "decision, shortest route",
             "decision, A* route", "agree?"],
            [[f"{row.parameter:.2f}", f"{float(row.posterior_h):.4f}",
              row.decision_shortest, row.decision_astar,
              "yes" if row.decision_shortest == row.decision_astar else "NO"]
             for row in sweep.rows],
            aligns="rrlll",
        )
        print()
        print("  " + summarise(sweep))

    print()
    print("  saved:", write_csv(prior_sweep, "sweep_prior.csv"))
    print("  saved:", write_csv(sensor_sweep, "sweep_sensor.csv"))
