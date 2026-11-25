"""Interactive adviser: the same four algorithms driven by keyboard input.

The static demonstration prints one fixed scenario. This mode lets the
resident type their own sensor readings and choose a route, and prints the
same recommendation the pipeline would produce for that input.
"""

from airoute import bayes, hmm, mdp, render, search
from airoute.scenario import ACTION_NAMES, SENSOR_SIGNALS

DEFAULT_READINGS = "alarm alarm calm"
ROUTES = {
    "1": ("shortest-distance route", search.bfs),
    "2": ("minimum-exposure route", search.astar),
}


def _ask(prompt, default):
    try:
        answer = input(prompt).strip()
    except EOFError:
        print()
        return default
    return answer or default


def _ask_readings():
    while True:
        raw = _ask(f"  readings, 1-3 hourly signals (alarm/calm) [{DEFAULT_READINGS}]: ", DEFAULT_READINGS)
        tokens = raw.replace(",", " ").split()
        if 1 <= len(tokens) <= 3 and all(token in SENSOR_SIGNALS for token in tokens):
            return tuple(tokens)
        print("  please enter one to three signals, each 'alarm' or 'calm'")


def _ask_route():
    while True:
        raw = _ask("  route: 1 = shortest, 2 = A* minimum exposure [2]: ", "2")
        if raw in ROUTES:
            return raw
        print("  enter 1 or 2")


def advise(readings, route_key):
    """Compute the recommendation for the given readings and route choice."""
    route_name, find_route = ROUTES[route_key]
    route = find_route()

    single = bayes.update(readings[0]) if len(readings) == 1 else None
    forward = hmm.forward(readings) if len(readings) > 1 else None
    viterbi = hmm.viterbi(readings) if len(readings) > 1 else None
    belief = single.belief if single else forward.final_belief

    decision = mdp.decide(belief, route.weight, route_name)
    return {
        "readings": readings,
        "single": single,
        "forward": forward,
        "viterbi": viterbi,
        "route": route,
        "route_name": route_name,
        "decision": decision,
    }


def _print_result(result):
    decision = result["decision"]
    route = result["route"]
    print()
    render.rule()
    print(f"  readings      {list(result['readings'])}")
    if result["single"]:
        posterior = result["single"].posterior_hazardous
        print(f"  Bayes         P(H) = {posterior} = {float(posterior):.1%} (prior 30.0%)")
    else:
        beliefs = result["forward"].beliefs
        print("  HMM forward   P(H): " + " -> ".join(f"{float(b['H']):.1%}" for b in beliefs))
        print(f"  Viterbi       {' -> '.join(result['viterbi'].sequence)}")
    print(f"  belief        P(H) = {float(decision.belief['H']):.1%}")
    print(f"  route         {result['route_name']}: {route.steps} steps, weight W = {route.weight}")
    print(f"  rewards       Q(Go) = {float(decision.q_values['Go']):+.3f}   "
          f"Q(Wait) = {float(decision.q_values['Wait']):+.3f}   "
          f"p* = {float(decision.threshold):.1%}")
    print()
    print(f"  {decision.action.upper()} - {ACTION_NAMES[decision.action]}")
    margin = decision.q_values[decision.action] - min(decision.q_values.values())
    print(f"  margin        {float(margin):+.3f} utility points")
    render.rule()


def run():
    """Ask for the readings and the route until the user stops."""
    render.rule("=")
    print("  CleanRoute Astana - interactive adviser")
    render.rule("=")
    print("  Type your own hourly readings and choose a route; the same four")
    print("  algorithms return the same recommendation the console demo prints.")
    print()

    while True:
        readings = _ask_readings()
        route_key = _ask_route()
        _print_result(advise(readings, route_key))
        print()
        if not _ask("  again? [y/N]: ", "n").lower().startswith("y"):
            break

    return 0
