"""Algorithm 4 (bonus) - Hidden Markov Model (Module 7: Hidden Markov Models).

Part 1 uses a single sensor reading. In reality the resident sees a whole
sequence of hourly readings, and a sequence carries more information than any
one of its elements: two alarms followed by a calm reading means something
different from three alarms in a row.

The same sensor model as in Part 1 is reused, so the HMM is consistent with the
Bayesian update rather than being a separate toy:

    hidden states  A (acceptable), H (hazardous)
    transitions    the hourly air-quality chain of the MDP
    emissions      P(alarm | H) = 0.85, P(alarm | A) = 0.20

Two standard HMM algorithms are implemented:

``viterbi``
    Decoding. The most likely hidden state *sequence* behind the readings.

``forward``
    Filtering. The probability of the hidden state *now*, given all readings so
    far. This is the belief that replaces the single-reading posterior when the
    MDP makes the final decision.
"""

from dataclasses import dataclass, field
from fractions import Fraction

from airoute.scenario import (
    EMISSIONS,
    INITIAL_DISTRIBUTION,
    STATES,
    TRANSITIONS,
)


@dataclass
class ViterbiResult:
    observations: tuple
    sequence: list
    probability: Fraction
    deltas: list
    psis: list
    steps: list = field(default_factory=list)


def viterbi(observations):
    """Most likely hidden state sequence for ``observations`` (exact fractions)."""
    observations = tuple(observations)
    if not observations:
        raise ValueError("the observation sequence is empty")
    for obs in observations:
        if obs not in ("alarm", "calm"):
            raise ValueError(f"unknown sensor signal: {obs!r}")

    delta = [
        {s: INITIAL_DISTRIBUTION[s] * EMISSIONS[s][observations[0]] for s in STATES}
    ]
    psi = [{s: None for s in STATES}]

    for t, obs in enumerate(observations[1:], start=1):
        current = {}
        back = {}
        for s in STATES:
            candidates = {prev: delta[t - 1][prev] * TRANSITIONS[prev][s] for prev in STATES}
            best_prev = max(candidates, key=lambda p: candidates[p])
            current[s] = candidates[best_prev] * EMISSIONS[s][obs]
            back[s] = best_prev
        delta.append(current)
        psi.append(back)

    last = max(STATES, key=lambda s: delta[-1][s])
    probability = delta[-1][last]

    sequence = [last]
    for t in range(len(observations) - 1, 0, -1):
        sequence.append(psi[t][sequence[-1]])
    sequence.reverse()

    steps = ["INPUT"]
    steps.append(f"  observations   {list(observations)}")
    steps.append(f"  initial pi     " + ", ".join(f"pi({s}) = {float(INITIAL_DISTRIBUTION[s])}" for s in STATES))
    for s in STATES:
        steps.append(
            "  transitions    " + ", ".join(f"P({s}->{n}) = {float(p)}" for n, p in TRANSITIONS[s].items())
        )
        steps.append(
            "  emissions      " + ", ".join(f"P({o}|{s}) = {float(p)}" for o, p in EMISSIONS[s].items())
        )
    steps += ["", "KEY CALCULATION - forward pass",
              "  delta_t(s) = max_s' [ delta_{t-1}(s') x P(s | s') ] x P(o_t | s)"]

    steps.append("  t = 1:  delta_1(s) = pi(s) x P(o_1 | s)")
    for s in STATES:
        steps.append(
            f"    delta_1({s}) = {float(INITIAL_DISTRIBUTION[s]):.4f} x "
            f"{float(EMISSIONS[s][observations[0]]):.4f} = {float(delta[0][s]):.6f}"
        )
    for t in range(1, len(observations)):
        steps.append(f"  t = {t + 1}:  o_{t + 1} = {observations[t]!r}")
        for s in STATES:
            parts = ", ".join(
                f"{float(delta[t - 1][p]):.6f} x {float(TRANSITIONS[p][s]):.2f} = "
                f"{float(delta[t - 1][p] * TRANSITIONS[p][s]):.6f} (from {p})"
                for p in STATES
            )
            steps.append(f"    delta_{t + 1}({s}): max({parts})")
            steps.append(
                f"      -> best predecessor {psi[t][s]}, "
                f"delta_{t + 1}({s}) = {float(delta[t][s]):.8f}, psi = {psi[t][s]}"
            )
    steps += ["", "KEY CALCULATION - backtrace",
              f"  t = {len(observations)}: argmax_s delta_T(s) = {last} with {float(probability):.8f}"]
    for t in range(len(observations) - 1, 0, -1):
        steps.append(f"  t = {t + 1}: psi_{t + 1}({sequence[t]}) = {sequence[t - 1]}  ->  state at t = {t} is {sequence[t - 1]}")
    steps += ["", "OUTPUT",
              f"  most likely hidden sequence: {sequence}",
              f"  joint probability of that sequence and the observations: {float(probability):.6f}"]

    return ViterbiResult(
        observations=observations,
        sequence=sequence,
        probability=probability,
        deltas=delta,
        psis=psi,
        steps=steps,
    )


@dataclass
class ForwardResult:
    observations: tuple
    alphas: list
    beliefs: list
    steps: list = field(default_factory=list)

    @property
    def final_belief(self):
        return dict(self.beliefs[-1])


def forward(observations):
    """Filtered belief after every reading (exact fractions, normalised each step)."""
    observations = tuple(observations)
    if not observations:
        raise ValueError("the observation sequence is empty")

    alpha = {s: INITIAL_DISTRIBUTION[s] * EMISSIONS[s][observations[0]] for s in STATES}
    total = sum(alpha.values())
    alphas = [dict(alpha)]
    beliefs = [{s: alpha[s] / total for s in STATES}]

    steps = ["INPUT", f"  observations   {list(observations)}", "",
             "KEY CALCULATION - forward recursion (unnormalised, then normalised)",
             "  alpha_t(s) = [ sum_s' alpha_{t-1}(s') x P(s | s') ] x P(o_t | s)"]
    steps.append(
        f"  t = 1:  alpha_1(A) = {float(alphas[0]['A']):.6f}, alpha_1(H) = {float(alphas[0]['H']):.6f}, "
        f"total = {float(total):.6f}"
    )
    steps.append(
        f"    filtered belief: P(A) = {float(beliefs[0]['A']):.4f}, P(H) = {float(beliefs[0]['H']):.4f}"
    )

    for t, obs in enumerate(observations[1:], start=1):
        predicted = {s: sum(alpha[p] * TRANSITIONS[p][s] for p in STATES) for s in STATES}
        alpha = {s: predicted[s] * EMISSIONS[s][obs] for s in STATES}
        total = sum(alpha.values())
        alphas.append(dict(alpha))
        beliefs.append({s: alpha[s] / total for s in STATES})
        steps.append(f"  t = {t + 1}:  o_{t + 1} = {obs!r}")
        for s in STATES:
            inner = " + ".join(
                f"{float(alphas[t - 1][p]):.6f} x {float(TRANSITIONS[p][s]):.2f}" for p in STATES
            )
            steps.append(f"    prediction  alpha~_{t + 1}({s}) = {inner} = {float(predicted[s]):.6f}")
            steps.append(
                f"    update      alpha_{t + 1}({s}) = {float(predicted[s]):.6f} x "
                f"{float(EMISSIONS[s][obs]):.4f} = {float(alpha[s]):.6f}"
            )
        steps.append(
            f"    normalised  P(A) = {float(beliefs[t]['A']):.4f}, P(H) = {float(beliefs[t]['H']):.4f}"
        )

    steps += ["", "OUTPUT"]
    for t, belief in enumerate(beliefs):
        steps.append(
            f"  belief after {t + 1} reading(s): P(H) = {float(belief['H']):.4f} = {float(belief['H']):.1%}"
        )

    return ForwardResult(
        observations=observations, alphas=alphas, beliefs=beliefs, steps=steps
    )


def explain(viterbi_result, forward_result):
    """The one-sentence explanation the project guidelines ask for."""
    return (
        f"Viterbi decodes the three readings {list(viterbi_result.observations)} into the hidden sequence "
        f"{viterbi_result.sequence}, and the forward recursion shows the filtered P(H) falling to "
        f"{float(forward_result.final_belief['H']):.1%}, so the MDP can decide on evidence from the whole "
        f"sequence instead of one noisy reading."
    )
