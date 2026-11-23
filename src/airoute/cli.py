"""Command-line demonstration: ``python -m airoute``.

Console output is the deliverable the project guidelines ask for. Each part
follows the same pattern required by the guidelines:

    INPUT -> KEY CALCULATION / STEPS -> OUTPUT -> one-sentence explanation
"""

import argparse
import json
import sys
from fractions import Fraction

from airoute import __author__, __course__, __version__, bayes, hmm, mdp, pipeline, render, search
from airoute.scenario import (
    ACTION_NAMES,
    ARRIVAL_BENEFIT,
    CONCENTRATION,
    DOSE_COST,
    GOAL,
    PRIOR_HAZARDOUS,
    SENSOR_FALSE_ALARM,
    SENSOR_SENSITIVITY,
    START,
    STATE_NAMES,
    TRANSITIONS,
)


def _json_default(value):
    if isinstance(value, Fraction):
        return {"fraction": str(value), "float": float(value)}
    if isinstance(value, tuple):
        return list(value)
    return str(value)


def header():
    render.rule("=")
    print("  CleanRoute Astana - a mini air-quality adviser for outdoor travel")
    print("  Final Project, AI Fundamentals")
    render.rule("=")
    print(f"  Student  : {__author__}")
    print(f"  Course   : {__course__}")
    print(f"  Version  : {__version__}")
    print()
    print("  REAL-WORLD PROBLEM")
    print("    On a winter evening in Astana, in the coal-heating season, a")
    print("    temperature inversion can trap particulates near the ground, so")
    print("    the air quality changes within an hour and differs from block to")
    print("    block. A resident has to decide two things: leave now or wait,")
    print("    and, if leaving, which way to walk.")
    print("    A city-wide AQI number answers neither question.")
    print()
    print("  SOLUTION - one pipeline, four course algorithms")
    print("    [1] Bayesian inference  (Module 6)  noisy sensor reading -> belief")
    print("    [2] A* search           (Modules 2-4) map -> minimum-exposure route")
    print("    [3] MDP                 (Module 5)  belief + route dose -> action")
    print("    [4] HMM / Viterbi       (Module 7)  reading sequence -> better belief")
    print()
    print("  ASSUMPTIONS (all inputs are hypothetical, as the guidelines allow)")
    print(f"    hidden states          A = {STATE_NAMES['A']}")
    print(f"                           H = {STATE_NAMES['H']}")
    print(f"    prior                  P(H) = {PRIOR_HAZARDOUS} = {float(PRIOR_HAZARDOUS):.1%}")
    print(f"    home sensor            P(alarm|H) = {SENSOR_SENSITIVITY} = {float(SENSOR_SENSITIVITY):.0%}, "
          f"P(alarm|A) = {SENSOR_FALSE_ALARM} = {float(SENSOR_FALSE_ALARM):.0%}")
    print(f"    air-quality chain      P(A->A) = {float(TRANSITIONS['A']['A'])}, "
          f"P(H->H) = {float(TRANSITIONS['H']['H'])} per hour")
    print(f"    reward model           R(s,Go) = {ARRIVAL_BENEFIT} - {float(DOSE_COST)} x C(s) x W(route),")
    print(f"                           C(A) = {CONCENTRATION['A']} and C(H) = {CONCENTRATION['H']} ug/m3 per weight unit,")
    print(f"                           W(route) = sum of the block weights on the route")
    print(f"    waiting cost           R(A,Wait) = -4, R(H,Wait) = -6 utility points")
    print(f"    discount               gamma = 0.9 per hour")
    print(f"    map                    6x6 blocks, weights 1..5, S = {START}, G = {GOAL}")
    print("    No real dataset and no trained model are used.")


def part_bayes(result, verbose=False):
    render.section(1, "BAYESIAN INFERENCE  (Module 6 - Probability and Bayesian Networks)")
    print("  Subproblem: a cheap home PM2.5 sensor is noisy. One raw reading")
    print("  cannot drive a decision, so it has to be combined with a prior.")
    render.subtitle("Case 1 - the sensor reports 'alarm'")
    render.steps(result.bayes_alarm.steps)
    print()
    print("  EXPLANATION:", bayes.explain(result.bayes_alarm))

    render.subtitle("Case 2 - the sensor reports 'calm' (the same model, other evidence)")
    calm = result.bayes_calm
    print("  INPUT")
    print(f"    prior P(H) = {calm.prior_hazardous}, observation e = 'calm'")
    print("  KEY CALCULATION")
    print(f"    P(calm|H) = 1 - {SENSOR_SENSITIVITY} = {1 - SENSOR_SENSITIVITY} = {float(1 - SENSOR_SENSITIVITY):.2f}")
    print(f"    P(calm|A) = 1 - {SENSOR_FALSE_ALARM} = {1 - SENSOR_FALSE_ALARM} = {float(1 - SENSOR_FALSE_ALARM):.2f}")
    print(f"    P(H|calm) = ({1 - SENSOR_SENSITIVITY} x {calm.prior_hazardous}) / "
          f"({(1 - SENSOR_SENSITIVITY) * calm.prior_hazardous} + {(1 - SENSOR_FALSE_ALARM) * (1 - calm.prior_hazardous)})")
    print("  OUTPUT")
    print(f"    P(H | calm) = {calm.posterior_hazardous} = {float(calm.posterior_hazardous):.4f} = {float(calm.posterior_hazardous):.1%}")
    print()
    print(f"  The same reading moves P(H) in opposite directions: 'alarm' raises it to")
    print(f"  {float(result.bayes_alarm.posterior_hazardous):.1%}, 'calm' lowers it to {float(calm.posterior_hazardous):.1%}.")
    print(f"  Likelihood ratio P(alarm|H)/P(alarm|A) = {result.bayes_alarm.likelihood_ratio} "
          f"= {float(result.bayes_alarm.likelihood_ratio):.2f}, so one alarm multiplies the")
    print(f"  odds of hazardous air by {float(result.bayes_alarm.likelihood_ratio):.2f}.")


def part_search(result, verbose=False):
    render.section(2, "A* SEARCH  (Modules 2-4 - Problem solving and search)")
    print("  Subproblem: if the resident leaves, which route minimises the inhaled")
    print("  dose? Each block carries a relative PM2.5 weight; the cost of a route")
    print("  is the sum of the weights of the blocks it passes through.")
    print()
    render.subtitle("The map")
    render.render_grid()

    render.subtitle("Algorithm 2a - BFS: the fewest steps")
    bfs = result.search_bfs
    print(f"  INPUT      S = (5,2), G = (0,5), every step costs 1")
    print(f"  STEPS      {bfs.expanded} nodes expanded, {bfs.generated} neighbours generated")
    if verbose:
        render.steps(bfs.steps_log)
    print(f"  OUTPUT     {bfs.steps} steps, route weight {bfs.weight}")
    render.render_grid(bfs.route)
    print(f"  route      {render.route_line(bfs.route)}")
    print(f"  weights    {render.route_weights(bfs.route)} = {bfs.weight}")
    print()
    print("  EXPLANATION: BFS expands level by level, so the first time it reaches the")
    print("  goal it holds a route with the fewest steps - but it is blind to pollution,")
    print(f"  and this {bfs.steps}-step route crosses {sum(1 for c in bfs.route if search.weight(c) >= 4)}")
    print(f"  weight-4 avenue blocks, for a total dose of {bfs.weight} weight units.")

    render.subtitle("Algorithm 2b - UCS (Dijkstra): the minimum exposure")
    ucs = result.search_ucs
    print(f"  INPUT      cost of entering a block = its PM2.5 weight")
    print(f"  STEPS      {ucs.expanded} nodes expanded, {ucs.generated} neighbours generated")
    if verbose:
        render.steps(ucs.trace)
    print(f"  OUTPUT     {ucs.steps} steps, route weight {ucs.weight}, optimal cost {ucs.goal_cost:.0f}")
    print()
    print("  EXPLANATION: UCS always expands the cheapest frontier node, so it is")
    print("  optimal for any non-negative cost - but with no heuristic it spreads in")
    print("  every direction and wastes expansions.")

    render.subtitle("Algorithm 2c - A*: the minimum exposure, with a heuristic")
    ast = result.search_astar
    print("  INPUT      g = exposure weight so far")
    print(f"             h = manhattan(n, G) x min cell weight = manhattan(n, G) x 1")
    print("             f = g + h")
    print(f"  STEPS      {ast.expanded} nodes expanded, {ast.generated} neighbours generated")
    if verbose:
        render.steps(ast.trace)
    else:
        render.steps(ast.trace[:6])
        print(f"  ... ({len(ast.trace) - 6} more expansions)")
    print(f"  OUTPUT     {ast.steps} steps, route weight {ast.weight}, optimal cost {ast.goal_cost:.0f}")
    render.render_grid(ast.route)
    print(f"  route      {render.route_line(ast.route)}")
    print(f"  weights    {render.route_weights(ast.route)} = {ast.weight}")
    print()
    print("  EXPLANATION:", search.explain(bfs, ast))
    print()
    print("  h is admissible (it never overestimates, because every remaining step")
    print("  costs at least 1) and consistent, therefore A* is guaranteed to return")
    print("  the same optimal cost as UCS - which it does, with fewer expansions.")
    render.table(
        ["algorithm", "steps", "exposure weight", "nodes expanded", "neighbours generated", "optimal cost"],
        [[r[k] for k in ("algorithm", "steps", "exposure weight", "nodes expanded",
                         "neighbours generated", "optimised cost")]
         for r in search.compare([bfs, ucs, ast])],
        aligns="lrrrrr",
    )


def part_mdp(result, verbose=False):
    render.section(3, "MARKOV DECISION PROCESS  (Module 5 - MDP and Reinforcement Learning)")
    print("  Subproblem: leave now or wait one hour? 'Go' ends the episode (the")
    print("  resident has arrived); 'Wait' costs an hour and the air then changes")
    print("  according to the transition matrix.")
    print()
    print("  ACTIONS")
    for action, meaning in ACTION_NAMES.items():
        print(f"    {action:<5} = {meaning}")

    render.subtitle("3a - One reading, the shortest-distance route (weight "
                    f"{result.search_bfs.weight})")
    render.steps(result.decision_single_baseline.steps)
    print()
    print("  EXPLANATION:", mdp.explain(result.decision_single_baseline))

    render.subtitle("3b - The same reading, the A* minimum-exposure route (weight "
                    f"{result.search_astar.weight})")
    render.steps(result.decision_single_optimal.steps)
    print()
    print("  EXPLANATION: only the reward table changed - the belief is identical -")
    print("  yet the recommendation flips, because a cleaner route lowers the health")
    print("  cost of going out and pushes the decision threshold up from "
          f"{float(result.decision_single_baseline.threshold):.1%} to "
          f"{float(result.decision_single_optimal.threshold):.1%}.")
    print("  This is the integration the project asks for: the search result is an")
    print("  input to the decision model, not a separate exercise.")

    render.subtitle("3c - Value iteration: what the route is worth in the long run")
    print("  Bellman backup, gamma = 0.9, 'Go' terminates the episode:")
    print("    V(s) = max( R(s, Go),  R(s, Wait) + gamma x sum_s' P(s'|s) V(s') )")
    print()
    base = result.policy_baseline
    opt = result.policy_optimal
    render.table(
        ["route", "V(A)", "V(H)", "policy in A", "policy in H", "iterations"],
        [
            [f"shortest (W = {base.route_weight})", f"{float(base.values['A']):+.4f}",
             f"{float(base.values['H']):+.4f}", base.policy["A"], base.policy["H"], base.iterations],
            [f"A* (W = {opt.route_weight})", f"{float(opt.values['A']):+.4f}",
             f"{float(opt.values['H']):+.4f}", opt.policy["A"], opt.policy["H"], opt.iterations],
        ],
        aligns="lrrllr",
    )
    gain_a = float(opt.values["A"]) - float(base.values["A"])
    gain_h = float(opt.values["H"]) - float(base.values["H"])
    print()
    print(f"  Planning the cleaner route raises the optimal value of clean air by")
    print(f"  {gain_a:+.4f} ({100 * gain_a / float(base.values['A']):+.1f}%) and of hazardous air by "
          f"{gain_h:+.4f}.")
    print()
    print("  EXPLANATION: value iteration converges to the same stationary policy in")
    print("  both cases - go when the air is acceptable, wait when it is hazardous -")
    print("  which confirms that the one-step comparison is not an artefact, and the")
    print("  higher values quantify the benefit of the route.")
    if verbose:
        render.subtitle("Convergence trace (shortest route)")
        render.steps(base.steps)


def part_hmm(result, verbose=False):
    render.section(4, "HIDDEN MARKOV MODEL  (Module 7 - HMM)  [bonus, fourth algorithm]")
    print("  Subproblem: the resident does not see one reading but three, one per")
    print("  hour. A sequence carries more information than a single element: two")
    print("  alarms followed by a calm reading is not the same as three alarms.")
    print()
    print("  The HMM reuses the Part 1 sensor model and the Part 3 transition")
    print("  matrix, so it is consistent with the rest of the pipeline.")

    render.subtitle("4a - Viterbi decoding: the most likely hidden sequence")
    render.steps(result.viterbi.steps if verbose else result.viterbi.steps[:14] + [
        f"  ... ({len(result.viterbi.steps) - 18} more lines, use --verbose)",
    ] + result.viterbi.steps[-4:])
    print()
    print("  EXPLANATION: Viterbi keeps only the most probable predecessor for each")
    print("  state at each step, so one backtrace recovers the whole hidden sequence")
    print("  instead of one state at a time.")

    render.subtitle("4b - Forward filtering: the belief after each reading")
    fwd = result.forward
    render.steps(fwd.steps if verbose else [
        "INPUT", f"  observations   {list(fwd.observations)}", "",
        "KEY CALCULATION",
        "  alpha_t(s) = [ sum_s' alpha_{t-1}(s') x P(s|s') ] x P(o_t | s), normalised",
        "", "OUTPUT",
    ] + fwd.steps[-3:])
    print()
    render.table(
        ["readings seen", "P(A)", "P(H)"],
        [[f"{list(fwd.observations)[:i + 1]}", f"{float(b['A']):.4f}", f"{float(b['H']):.4f}"]
         for i, b in enumerate(fwd.beliefs)],
        aligns="lrr",
    )
    print()
    print("  EXPLANATION:", hmm.explain(result.viterbi, fwd))
    print()
    print(f"  The second reading makes the air look worse ({float(fwd.beliefs[1]['H']):.1%}),")
    print(f"  the third makes it much better ({float(fwd.beliefs[2]['H']):.1%}). A single-reading")
    print("  adviser could not see either of those turns.")

    render.subtitle("4c - Final decision with the filtered belief")
    for label, decision in (("shortest-distance route", result.decision_sequence_baseline),
                            ("A* minimum-exposure route", result.decision_sequence_optimal)):
        print(f"  {label:<26} W = {decision.route_weight:<3} "
              f"Q(Go) = {float(decision.q_values['Go']):+.4f}  "
              f"Q(Wait) = {float(decision.q_values['Wait']):+.4f}  "
              f"p* = {float(decision.threshold):.4f}  ->  {decision.action}")
    print()
    print("  With three readings the recommendation is 'Go' for both routes: the")
    print("  temporal evidence alone is strong enough, and route planning adds margin.")


def part_experiments(result, verbose=False):
    from airoute import experiments

    render.section(5, "EXPERIMENTS - HOW SENSITIVE IS THE RECOMMENDATION?")
    print("  The scenario numbers are hypothetical, so the honest question is not")
    print("  'is the answer right' but 'which assumptions change the answer'.")
    print()
    prior_sweep, sensor_sweep = experiments.run(
        result.search_bfs.weight, result.search_astar.weight
    )
    for sweep in (prior_sweep, sensor_sweep):
        render.subtitle(f"{sweep.name}: sweep of {sweep.parameter_name}")
        render.table(
            [sweep.parameter_name, "P(H | alarm)", "shortest route", "A* route", "agree?"],
            [[f"{row.parameter:.2f}", f"{float(row.posterior_h):.4f}",
              row.decision_shortest, row.decision_astar,
              "yes" if row.decision_shortest == row.decision_astar else "NO"]
             for row in sweep.rows],
            aligns="rrlll",
        )
        print()
        print("  " + experiments.summarise(sweep))
        print()
    print("  The scenario prior P(H) = 0.30 sits inside the disagreement band of the")
    print("  prior sweep, which is exactly why this project is interesting: here the")
    print("  route is not decoration, it changes the recommendation.")


def part_summary(result, verbose=False):
    render.section(6, "INTEGRATION AND RESULTS")
    print("  How the four algorithms form one system:")
    print()
    print("    sensor 'alarm' --[1 Bayes]--> P(H) = "
          f"{float(result.bayes_alarm.posterior_hazardous):.1%}")
    print("                                     |")
    print("    6x6 map --------[2 A*]---------+--|--> route weight W = "
          f"{result.search_astar.weight} (vs {result.search_bfs.weight} for BFS)")
    print("                                     |")
    print("                          [3 MDP]  R(s,Go) = 12 - 0.02 x C(s) x W")
    print("                                     |")
    print("    3 readings ----[4 HMM forward]--> P(H) = "
          f"{float(result.forward.final_belief['H']):.1%}")
    print("                                     |")
    print("                                     v")
    print(f"                          {result.recommendation['action']} now, "
          f"{result.recommendation['route_steps']} steps through the park belt")
    print()
    render.subtitle("Summary of results")
    render.table(["#", "result"], pipeline.results_table(result), aligns="ll")

    render.subtitle("Answer to the resident")
    rec = result.recommendation
    print(f"  Recommendation : {rec['action']} - {ACTION_NAMES[rec['action']]}")
    print(f"  Why            : P(hazardous) = {float(rec['belief_hazardous']):.1%} is below the")
    print(f"                   exact decision threshold p* = {float(rec['threshold']):.1%}")
    print(f"  Route          : {rec['route_steps']} steps, exposure weight {rec['route_weight']}")
    print(f"  Hidden states  : Viterbi says the last three hours were {rec['hidden_sequence']}")
    print(f"  Margin         : Q(Go) - Q(Wait) = {float(rec['margin']):+.3f} utility points")
    print()
    print("  WHAT WOULD IMPROVE THE PROJECT")
    print("    * replace the hypothetical sensor model with a calibrated low-cost")
    print("      sensor, and estimate its sensitivity and false-alarm rate from data;")
    print("    * estimate the transition matrix from an hourly AQI time series")
    print("      instead of assuming it, and learn the policy with Q-learning;")
    print("    * model exposure per unit of effort, so a steep or longer route costs")
    print("      more breaths per block;")
    print("    * extend the MDP to more than two states and to a finite deadline,")
    print("      which turns 'wait' into a genuine scheduling decision;")
    print("    * serve the pipeline over an API so that it can be reused by other")
    print("      courses and expanded into a larger project.")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m airoute",
        description="CleanRoute Astana - AI Fundamentals Final Project demonstration.",
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="print the full search and HMM traces")
    parser.add_argument("--section", choices=["all", "bayes", "search", "mdp", "hmm",
                                               "experiments", "summary"],
                        default="all", help="run one part only (default: all)")
    parser.add_argument("--json", metavar="PATH", help="also write every result to a JSON file")
    parser.add_argument("--no-header", action="store_true", help="skip the scenario header")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    result = pipeline.run()

    if not args.no_header:
        header()

    parts = {
        "bayes": part_bayes,
        "search": part_search,
        "mdp": part_mdp,
        "hmm": part_hmm,
        "experiments": part_experiments,
        "summary": part_summary,
    }
    selected = list(parts) if args.section == "all" else [args.section]
    for name in selected:
        parts[name](result, verbose=args.verbose)

    if args.json:
        payload = {
            "bayes": {
                "alarm": {"posterior_H": str(result.bayes_alarm.posterior_hazardous),
                          "posterior_H_float": float(result.bayes_alarm.posterior_hazardous)},
                "calm": {"posterior_H": str(result.bayes_calm.posterior_hazardous),
                         "posterior_H_float": float(result.bayes_calm.posterior_hazardous)},
            },
            "search": [
                {"algorithm": r.algorithm, "route": r.route, "steps": r.steps,
                 "weight": r.weight, "expanded": r.expanded, "generated": r.generated}
                for r in (result.search_bfs, result.search_ucs, result.search_astar)
            ],
            "mdp": {
                "single_reading": {
                    "shortest_route": {"action": result.decision_single_baseline.action,
                                       "threshold": float(result.decision_single_baseline.threshold),
                                       "Q": {k: float(v) for k, v in result.decision_single_baseline.q_values.items()}},
                    "astar_route": {"action": result.decision_single_optimal.action,
                                    "threshold": float(result.decision_single_optimal.threshold),
                                    "Q": {k: float(v) for k, v in result.decision_single_optimal.q_values.items()}},
                },
                "value_iteration": {
                    "shortest_route": {"V": {k: float(v) for k, v in result.policy_baseline.values.items()},
                                       "policy": result.policy_baseline.policy,
                                       "iterations": result.policy_baseline.iterations},
                    "astar_route": {"V": {k: float(v) for k, v in result.policy_optimal.values.items()},
                                    "policy": result.policy_optimal.policy,
                                    "iterations": result.policy_optimal.iterations},
                },
                "three_readings": {
                    "shortest_route": {"action": result.decision_sequence_baseline.action,
                                       "threshold": float(result.decision_sequence_baseline.threshold)},
                    "astar_route": {"action": result.decision_sequence_optimal.action,
                                    "threshold": float(result.decision_sequence_optimal.threshold)},
                },
            },
            "hmm": {
                "observations": list(result.viterbi.observations),
                "viterbi_sequence": result.viterbi.sequence,
                "filtered_beliefs_H": [float(b["H"]) for b in result.forward.beliefs],
            },
            "recommendation": {
                "action": result.recommendation["action"],
                "route": result.recommendation["route"],
                "route_steps": result.recommendation["route_steps"],
                "route_weight": result.recommendation["route_weight"],
                "belief_H": float(result.recommendation["belief_hazardous"]),
                "threshold": float(result.recommendation["threshold"]),
            },
        }
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=_json_default)
        print()
        print(f"  results written to {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
