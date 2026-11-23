"""Algorithm 3 - Search (Modules 2-4: Problem solving and search).

Three search algorithms run on the same 6x6 map of city blocks:

``bfs``
    Breadth-first search. Every step costs 1, so BFS returns a route with the
    **fewest steps** - what an ordinary navigation app would suggest.

``ucs``
    Uniform-cost search (Dijkstra). The cost of entering a block is its PM2.5
    weight, so UCS returns a **minimum-exposure** route. It explores blindly,
    in every direction at once.

``astar``
    A* = UCS plus the admissible heuristic
    ``h(n) = manhattan(n, goal) x min_cell_weight``.
    It returns the same minimum-exposure route as UCS but expands fewer nodes,
    because the heuristic tells it which direction is promising.

The comparison of expanded nodes and of route doses is the measurable result of
this part, and the winning route is what feeds back into the MDP.
"""

import heapq
from collections import deque
from dataclasses import dataclass, field

from airoute.scenario import (
    GOAL,
    GRID,
    MIN_CELL_WEIGHT,
    NEIGHBOUR_ORDER,
    START,
)


@dataclass
class SearchResult:
    """One route found by one search algorithm."""

    algorithm: str
    route: list
    steps: int
    weight: int                 # sum of PM2.5 weights of all cells on the route
    expanded: int               # nodes taken out of the frontier
    generated: int              # neighbours put into the frontier
    goal_cost: float            # the cost the algorithm actually optimised
    trace: list = field(default_factory=list)
    steps_log: list = field(default_factory=list)

    @property
    def found(self):
        return bool(self.route)


def weight(cell):
    """PM2.5 weight of a block, or None when the block is impassable."""
    row, col = cell
    return GRID[row][col]


def is_open(cell):
    row, col = cell
    return 0 <= row < len(GRID) and 0 <= col < len(GRID[0]) and GRID[row][col] is not None


def neighbours(cell):
    """Passable orthogonal neighbours, in a fixed order for reproducibility."""
    row, col = cell
    result = []
    for d_row, d_col in NEIGHBOUR_ORDER:
        candidate = (row + d_row, col + d_col)
        if is_open(candidate):
            result.append(candidate)
    return result


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def heuristic(cell):
    """Admissible and consistent A* heuristic.

    Every remaining step enters a block whose weight is at least
    ``MIN_CELL_WEIGHT``, so the Manhattan distance times that minimum never
    overestimates the true remaining exposure cost.
    """
    return manhattan(cell, GOAL) * MIN_CELL_WEIGHT


def route_weight(route):
    return sum(weight(cell) for cell in route)


def _reconstruct(came_from, current):
    route = [current]
    while current in came_from:
        current = came_from[current]
        route.append(current)
    route.reverse()
    return route


def bfs(start=START, goal=GOAL):
    """Breadth-first search: a route with the fewest steps."""
    frontier = deque([start])
    came_from = {}
    seen = {start}
    expanded = 0
    generated = 0
    log = []
    route = []

    while frontier:
        current = frontier.popleft()
        expanded += 1
        log.append(f"  expand #{expanded:<3} {current}  g(steps) = {len(_reconstruct(came_from, current)) - 1}")
        if current == goal:
            route = _reconstruct(came_from, current)
            break
        for nxt in neighbours(current):
            generated += 1
            if nxt not in seen:
                seen.add(nxt)
                came_from[nxt] = current
                frontier.append(nxt)

    return SearchResult(
        algorithm="BFS (fewest steps)",
        route=route,
        steps=len(route) - 1 if route else -1,
        weight=route_weight(route) if route else -1,
        expanded=expanded,
        generated=generated,
        goal_cost=float(len(route) - 1) if route else float("inf"),
        steps_log=log,
    )


def ucs(start=START, goal=GOAL):
    """Uniform-cost search (Dijkstra) on exposure weight: the minimum-dose route."""
    return _best_first(start, goal, use_heuristic=False, name="UCS / Dijkstra (minimum exposure)")


def astar(start=START, goal=GOAL):
    """A* on exposure weight with an admissible heuristic: the minimum-dose route."""
    return _best_first(start, goal, use_heuristic=True, name="A* (minimum exposure)")


def _best_first(start, goal, use_heuristic, name):
    """Shared body of UCS and A*.

    The only difference is whether ``h`` is added to ``g`` when ordering the
    frontier, which makes the node-expansion comparison a fair one: both runs
    use the same cost model, the same tie-breaking and the same closed set.

    ``g`` already contains the weight of the start block, so the final cost is
    the sum of the weights of every block on the route, start and goal included.
    """
    counter = 0
    g_score = {start: weight(start)}
    came_from = {}
    closed = set()
    h_start = heuristic(start) if use_heuristic else 0
    frontier = [(g_score[start] + h_start, h_start, counter, start)]
    expanded = 0
    generated = 0
    log = []
    route = []

    while frontier:
        f, h, _, current = heapq.heappop(frontier)
        if current in closed:
            continue
        closed.add(current)
        expanded += 1
        g = g_score[current]
        if use_heuristic:
            log.append(f"  expand #{expanded:<3} {current}  w = {weight(current)}  g = {g:<3} h = {h:<3} f = {f}")
        else:
            log.append(f"  expand #{expanded:<3} {current}  w = {weight(current)}  g = {g}")
        if current == goal:
            route = _reconstruct(came_from, current)
            break
        for nxt in neighbours(current):
            generated += 1
            if nxt in closed:
                continue
            tentative = g + weight(nxt)
            if tentative < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative
                came_from[nxt] = current
                counter += 1
                h_next = heuristic(nxt) if use_heuristic else 0
                heapq.heappush(frontier, (tentative + h_next, h_next, counter, nxt))

    return SearchResult(
        algorithm=name,
        route=route,
        steps=len(route) - 1 if route else -1,
        weight=route_weight(route) if route else -1,
        expanded=expanded,
        generated=generated,
        goal_cost=float(g_score[goal]) if goal in g_score and route else float("inf"),
        trace=log,
    )


def compare(results):
    """Side-by-side rows for the search comparison table."""
    return [
        {
            "algorithm": r.algorithm,
            "steps": r.steps,
            "exposure weight": r.weight,
            "nodes expanded": r.expanded,
            "neighbours generated": r.generated,
            "optimised cost": r.goal_cost,
        }
        for r in results
    ]


def explain(bfs_result, astar_result):
    """The one-sentence explanation the project guidelines ask for."""
    saving = bfs_result.weight - astar_result.weight
    percent = 100.0 * saving / bfs_result.weight if bfs_result.weight else 0.0
    return (
        f"A* trades {astar_result.steps - bfs_result.steps} extra steps for a route through cleaner blocks, "
        f"cutting the inhaled dose from {bfs_result.weight} to {astar_result.weight} weight units "
        f"(-{percent:.1f}%), and it reaches that optimum after expanding {astar_result.expanded} nodes "
        f"against {bfs_result.expanded} for BFS."
    )
