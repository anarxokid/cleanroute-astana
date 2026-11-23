"""Algorithm 2 - Markov decision process (Module 5: MDP and Reinforcement Learning).

Two states of the air, two actions, a given transition matrix and a given
reward table - exactly the toy MDP the project guidelines describe. The module
does two things with it.

1. **One-step expected reward under a belief.** The Bayesian posterior is not a
   fact, it is a distribution, so the immediate value of an action is its
   expectation over that distribution::

       Q(b, a) = sum_s b(s) * R(s, a)

   The action with the larger Q is the recommendation. This also gives an exact
   **decision threshold** ``p*``: leave now only if ``P(H) < p*``.

2. **Value iteration over the long run.** "Go" ends the episode because the
   resident has arrived; "Wait" costs an hour and the air then changes
   according to the transition matrix::

       V(s) = max( R(s, Go),
                   R(s, Wait) + gamma * sum_s' P(s'|s) V(s') )

   Iterating this Bellman backup to a fixed point yields the optimal
   stationary policy and shows how much the route choice is worth in the long
   run.

The integration point with the search is :func:`airoute.scenario.reward_go`:
the exposure weight of the chosen route enters ``R(s, Go)`` directly.
"""

from dataclasses import dataclass, field
from fractions import Fraction

from airoute.scenario import (
    ACTIONS,
    DISCOUNT,
    REWARD_WAIT,
    STATES,
    TRANSITIONS,
    reward_go,
)

#: Bellman backups are stopped when no state value moves by more than this.
TOLERANCE = Fraction(1, 10 ** 9)
MAX_ITERATIONS = 500


def reward_table(route_weight):
    """R(s, a) for a route whose total block weight is ``route_weight``."""
    return {
        state: {"Go": reward_go(state, route_weight), "Wait": REWARD_WAIT[state]}
        for state in STATES
    }


@dataclass
class BeliefDecision:
    """Result of the one-step expected-reward comparison under a belief."""

    route_weight: int
    belief: dict
    rewards: dict
    q_values: dict
    action: str
    threshold: Fraction
    steps: list = field(default_factory=list)


def decide(belief, route_weight, route_name="route"):
    """One-step expected reward for each action; pick the larger one.

    Parameters
    ----------
    belief:
        ``{"A": Fraction, "H": Fraction}`` summing to 1, e.g. a Bayes posterior.
    route_weight:
        Total PM2.5 block weight of the route that "Go" would use.
    """
    rewards = reward_table(route_weight)

    q = {}
    for action in ACTIONS:
        q[action] = sum(belief[state] * rewards[state][action] for state in STATES)

    action = max(ACTIONS, key=lambda a: q[a])

    # Exact threshold: Go beats Wait when (1-p)*dA + p*dH > 0 with
    # dA = R(A,Go) - R(A,Wait) and dH = R(H,Go) - R(H,Wait), i.e. p < dA/(dA-dH).
    d_a = rewards["A"]["Go"] - rewards["A"]["Wait"]
    d_h = rewards["H"]["Go"] - rewards["H"]["Wait"]
    threshold = d_a / (d_a - d_h) if d_a != d_h else Fraction(1)

    p_h = belief["H"]
    steps = [
        "INPUT",
        f"  belief from Bayes   P(A) = {belief['A']} = {float(belief['A']):.4f}, "
        f"P(H) = {belief['H']} = {float(belief['H']):.4f}",
        f"  {route_name} weight  W = {route_weight} block-weight units",
        "",
        "REWARD TABLE  R(state, action) = arrival benefit - dose cost x concentration x W",
    ]
    for state in STATES:
        steps.append(
            f"  R({state}, Go)   = {rewards[state]['Go']:>9} = {float(rewards[state]['Go']):+.3f}"
            f"      R({state}, Wait) = {rewards[state]['Wait']:>4} = {float(rewards[state]['Wait']):+.3f}"
        )
    steps += [
        "",
        "KEY CALCULATION  Q(b, a) = sum_s b(s) x R(s, a)",
    ]
    for a in ACTIONS:
        terms = " + ".join(
            f"{float(belief[s]):.4f} x ({float(rewards[s][a]):+.3f})" for s in STATES
        )
        steps.append(f"  Q(b, {a:<4}) = {terms} = {float(q[a]):+.4f}   (exact {q[a]})")
    steps += [
        "",
        "DECISION THRESHOLD  (exact)",
        f"  dA = R(A,Go) - R(A,Wait) = {float(d_a):+.3f}",
        f"  dH = R(H,Go) - R(H,Wait) = {float(d_h):+.3f}",
        f"  p* = dA / (dA - dH) = {threshold} = {float(threshold):.4f} = {float(threshold):.2%}",
        f"  Go now is better exactly when P(H) < p* = {float(threshold):.2%}",
        "",
        "OUTPUT",
        f"  P(H) = {float(p_h):.2%} {'<' if p_h < threshold else '>='} p* = {float(threshold):.2%} "
        f"-> recommended action: {action}",
    ]

    return BeliefDecision(
        route_weight=route_weight,
        belief=dict(belief),
        rewards=rewards,
        q_values=q,
        action=action,
        threshold=threshold,
        steps=steps,
    )


@dataclass
class PolicyResult:
    """Result of value iteration."""

    route_weight: int
    values: dict
    policy: dict
    iterations: int
    history: list
    steps: list = field(default_factory=list)


def value_iteration(route_weight, discount=DISCOUNT, tolerance=TOLERANCE,
                    max_iterations=MAX_ITERATIONS, record_history=True):
    """Bellman backups to a fixed point; "Go" is a terminating action.

    Returns the optimal values, the optimal stationary policy and the full
    convergence history so that the fixed point can be inspected.
    """
    rewards = reward_table(route_weight)
    values = {state: Fraction(0) for state in STATES}
    history = [{"iteration": 0, "V(A)": values["A"], "V(H)": values["H"], "delta": None}]
    policy = {}
    iterations = 0
    steps = [
        "INPUT",
        f"  discount gamma = {discount} = {float(discount)}",
        f"  route weight W = {route_weight}",
        "  transitions P(s' | s):",
    ]
    for state in STATES:
        row = ", ".join(f"P({n}|{state}) = {float(p)}" for n, p in TRANSITIONS[state].items())
        steps.append(f"    from {state}: {row}")
    steps += [
        "",
        "BELLMAN BACKUP  (Go terminates the episode, so it has no continuation value)",
        "  V(s) = max( R(s, Go),  R(s, Wait) + gamma x sum_s' P(s'|s) V(s') )",
        "",
        "KEY CALCULATION - iteration by iteration",
    ]

    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        new_values = {}
        for state in STATES:
            go_value = rewards[state]["Go"]
            continuation = sum(TRANSITIONS[state][nxt] * values[nxt] for nxt in STATES)
            wait_value = rewards[state]["Wait"] + discount * continuation
            new_values[state] = max(go_value, wait_value)
            policy[state] = "Go" if go_value >= wait_value else "Wait"

        delta = max(abs(new_values[s] - values[s]) for s in STATES)
        values = new_values
        if record_history:
            history.append({
                "iteration": iteration,
                "V(A)": values["A"],
                "V(H)": values["H"],
                "delta": delta,
            })
        if iteration <= 6 or delta >= tolerance:
            if iteration <= 8:
                steps.append(
                    f"  k = {iteration}: V(A) = {float(values['A']):+.6f}, "
                    f"V(H) = {float(values['H']):+.6f}, max change = {float(delta):.3e}"
                )
        if delta < tolerance:
            steps.append(f"  ... converged at k = {iteration}, max change = {float(delta):.3e} < {float(tolerance):.1e}")
            break

    steps += [
        "",
        "OUTPUT",
        f"  optimal values   V(A) = {float(values['A']):+.4f}, V(H) = {float(values['H']):+.4f}",
        f"  optimal policy   {policy['A']} in Acceptable air, {policy['H']} in Hazardous air",
        f"  iterations       {iterations}",
    ]

    return PolicyResult(
        route_weight=route_weight,
        values=values,
        policy=policy,
        iterations=iterations,
        history=history,
        steps=steps,
    )


def explain(decision):
    """The one-sentence explanation the project guidelines ask for."""
    return (
        f"The MDP turns the belief P(H) = {float(decision.belief['H']):.1%} into an action by comparing "
        f"one-step expected rewards (Go {float(decision.q_values['Go']):+.2f} vs Wait "
        f"{float(decision.q_values['Wait']):+.2f}) against the exact threshold "
        f"p* = {float(decision.threshold):.1%}, which is where the health cost of the trip "
        f"outweighs the cost of losing an hour."
    )
