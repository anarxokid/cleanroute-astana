"""Integration: the four algorithms as one decision pipeline.

This module is the answer to the requirement that the algorithms "must
contribute to a common project goal" and not be three unrelated demos.

    home PM2.5 sensor
            |
            v
    [1] Bayesian inference  ----> belief b0 = P(A), P(H)
            |                                   ^
            v                                   |
    [2] MDP one-step expected reward            |
            |                                   |
            |   action = "Go"?                  |
            v                                   |
    [3] A* minimum-exposure route               |
            |                                   |
            | route weight W enters R(s, Go)    |
            +-----------------------------------+
            |
    [4] HMM forward / Viterbi over three hourly readings
            |
            v
    refined belief b2 -> final MDP decision -> recommendation

Two feedback arrows make it a single system rather than four exercises:

* the exposure weight found by A* changes the MDP reward ``R(s, Go)``, and can
  therefore change the recommended action;
* the filtered belief from the HMM replaces the single-reading posterior, which
  again changes the MDP input.
"""

from dataclasses import dataclass, field

from airoute import bayes, hmm, mdp, search
from airoute.scenario import OBSERVATION, OBSERVATION_SEQUENCE


@dataclass
class PipelineResult:
    """Everything the pipeline computed, so it can be reused and tested."""

    bayes_alarm: bayes.BayesResult = None
    bayes_calm: bayes.BayesResult = None
    search_bfs: search.SearchResult = None
    search_ucs: search.SearchResult = None
    search_astar: search.SearchResult = None
    decision_single_baseline: mdp.BeliefDecision = None
    decision_single_optimal: mdp.BeliefDecision = None
    policy_baseline: mdp.PolicyResult = None
    policy_optimal: mdp.PolicyResult = None
    viterbi: hmm.ViterbiResult = None
    forward: hmm.ForwardResult = None
    decision_sequence_baseline: mdp.BeliefDecision = None
    decision_sequence_optimal: mdp.BeliefDecision = None
    recommendation: dict = field(default_factory=dict)

    @property
    def dose_reduction(self):
        before = self.search_bfs.weight
        after = self.search_astar.weight
        return before - after, 100.0 * (before - after) / before


def run(observation=OBSERVATION, sequence=OBSERVATION_SEQUENCE):
    """Execute the whole pipeline once and return every intermediate result."""
    result = PipelineResult()

    # --- Part 1: one noisy reading becomes a calibrated belief ---------------
    result.bayes_alarm = bayes.update("alarm")
    result.bayes_calm = bayes.update("calm")
    belief_single = result.bayes_alarm.belief if observation == "alarm" else result.bayes_calm.belief

    # --- Part 3: plan both candidate routes ---------------------------------
    result.search_bfs = search.bfs()
    result.search_ucs = search.ucs()
    result.search_astar = search.astar()

    # --- Part 2: the same belief, the two different routes ------------------
    result.decision_single_baseline = mdp.decide(
        belief_single, result.search_bfs.weight, "shortest-distance route"
    )
    result.decision_single_optimal = mdp.decide(
        belief_single, result.search_astar.weight, "minimum-exposure route"
    )
    result.policy_baseline = mdp.value_iteration(result.search_bfs.weight)
    result.policy_optimal = mdp.value_iteration(result.search_astar.weight)

    # --- Part 4: three readings instead of one ------------------------------
    result.viterbi = hmm.viterbi(sequence)
    result.forward = hmm.forward(sequence)
    belief_sequence = result.forward.final_belief

    result.decision_sequence_baseline = mdp.decide(
        belief_sequence, result.search_bfs.weight, "shortest-distance route"
    )
    result.decision_sequence_optimal = mdp.decide(
        belief_sequence, result.search_astar.weight, "minimum-exposure route"
    )

    # --- Final recommendation ----------------------------------------------
    final = result.decision_sequence_optimal
    result.recommendation = {
        "action": final.action,
        "belief_hazardous": belief_sequence["H"],
        "threshold": final.threshold,
        "route": result.search_astar.route,
        "route_steps": result.search_astar.steps,
        "route_weight": result.search_astar.weight,
        "margin": final.q_values[final.action] - min(final.q_values.values()),
        "hidden_sequence": result.viterbi.sequence,
    }
    return result


def results_table(result):
    """The summary of results required by the project checklist."""
    saving, percent = result.dose_reduction
    single_base = result.decision_single_baseline
    single_opt = result.decision_single_optimal
    seq_base = result.decision_sequence_baseline
    seq_opt = result.decision_sequence_optimal

    rows = [
        ("1. Bayes, one reading 'alarm'",
         f"P(H) = {result.bayes_alarm.posterior_hazardous} = {float(result.bayes_alarm.posterior_hazardous):.1%} "
         f"(prior 30.0%)"),
        ("1b. Bayes, one reading 'calm'",
         f"P(H) = {result.bayes_calm.posterior_hazardous} = {float(result.bayes_calm.posterior_hazardous):.1%}"),
        ("2. BFS, fewest steps",
         f"{result.search_bfs.steps} steps, exposure weight {result.search_bfs.weight}, "
         f"{result.search_bfs.expanded} nodes expanded"),
        ("2b. UCS, minimum exposure",
         f"{result.search_ucs.steps} steps, exposure weight {result.search_ucs.weight}, "
         f"{result.search_ucs.expanded} nodes expanded"),
        ("2c. A*, minimum exposure",
         f"{result.search_astar.steps} steps, exposure weight {result.search_astar.weight}, "
         f"{result.search_astar.expanded} nodes expanded"),
        ("2d. Dose reduction by A*",
         f"{saving} weight units, -{percent:.1f}%, for {result.search_astar.steps - result.search_bfs.steps} extra steps"),
        ("3. MDP, one reading + shortest route",
         f"Q(Go) = {float(single_base.q_values['Go']):+.3f}, Q(Wait) = {float(single_base.q_values['Wait']):+.3f}, "
         f"p* = {float(single_base.threshold):.1%} -> {single_base.action}"),
        ("3b. MDP, one reading + A* route",
         f"Q(Go) = {float(single_opt.q_values['Go']):+.3f}, Q(Wait) = {float(single_opt.q_values['Wait']):+.3f}, "
         f"p* = {float(single_opt.threshold):.1%} -> {single_opt.action}"),
        ("3c. Value iteration, shortest route",
         f"V(A) = {float(result.policy_baseline.values['A']):+.4f}, "
         f"V(H) = {float(result.policy_baseline.values['H']):+.4f}, "
         f"policy = {result.policy_baseline.policy['A']}/{result.policy_baseline.policy['H']}, "
         f"{result.policy_baseline.iterations} iterations"),
        ("3d. Value iteration, A* route",
         f"V(A) = {float(result.policy_optimal.values['A']):+.4f}, "
         f"V(H) = {float(result.policy_optimal.values['H']):+.4f}, "
         f"policy = {result.policy_optimal.policy['A']}/{result.policy_optimal.policy['H']}, "
         f"{result.policy_optimal.iterations} iterations"),
        ("4. Viterbi, three readings",
         f"{list(result.viterbi.observations)} -> hidden sequence {result.viterbi.sequence}"),
        ("4b. Forward filtering",
         "P(H) after 1/2/3 readings = "
         + ", ".join(f"{float(b['H']):.1%}" for b in result.forward.beliefs)),
        ("4c. MDP, three readings + shortest route",
         f"Q(Go) = {float(seq_base.q_values['Go']):+.3f}, p* = {float(seq_base.threshold):.1%} -> {seq_base.action}"),
        ("4d. MDP, three readings + A* route",
         f"Q(Go) = {float(seq_opt.q_values['Go']):+.3f}, p* = {float(seq_opt.threshold):.1%} -> {seq_opt.action}"),
        ("FINAL RECOMMENDATION",
         f"{result.recommendation['action']} now, {result.recommendation['route_steps']}-step route "
         f"through the park belt, P(H) = {float(result.recommendation['belief_hazardous']):.1%} "
         f"< p* = {float(result.recommendation['threshold']):.1%}"),
    ]
    return rows
