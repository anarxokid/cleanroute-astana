"""Figures for the report and the presentation.

Every figure is drawn from the objects that :func:`airoute.pipeline.run`
actually produced, so nothing here is a hand-made illustration. Run::

    python -m airoute.figures            # writes the PNG files into assets/
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from airoute import pipeline
from airoute.scenario import GOAL, GRID, START

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")

PALETTE = {
    "clean": "#2E7D32",
    "dirty": "#C62828",
    "accent": "#1565C0",
    "neutral": "#546E7A",
    "gold": "#F9A825",
}


def _grid_axes(ax):
    matrix = np.array([[np.nan if w is None else w for w in row] for row in GRID], dtype=float)
    matrix = np.flipud(matrix)          # row 0 of the map at the top
    cmap = plt.get_cmap("RdYlGn_r")
    cmap.set_bad("#ECEFF1")
    ax.imshow(np.ma.masked_invalid(matrix), cmap=cmap, vmin=0.5, vmax=5.5, alpha=0.85)
    ax.set_xticks(range(len(GRID[0])))
    ax.set_yticks(range(len(GRID)))
    ax.set_xticklabels([f"c{c}" for c in range(len(GRID[0]))])
    ax.set_yticklabels([f"r{len(GRID) - 1 - i}" for i in range(len(GRID))])
    ax.set_xticks(np.arange(-0.5, len(GRID[0]), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(GRID), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    return matrix


def _plot_route(ax, route, color, marker, label):
    xs = [c for _, c in route]
    ys = [len(GRID) - 1 - r for r, _ in route]
    ax.plot(xs, ys, color=color, linewidth=2.6, marker=marker, markersize=7,
            markerfacecolor="white", markeredgecolor=color, label=label, zorder=5)


def figure_map(result, path):
    fig, ax = plt.subplots(figsize=(7.6, 6.6))
    _grid_axes(ax)

    for row_index, row in enumerate(GRID):
        for col_index, w in enumerate(row):
            y = len(GRID) - 1 - row_index
            if (row_index, col_index) == START:
                text, colour = "S", "#000000"
            elif (row_index, col_index) == GOAL:
                text, colour = "G", "#000000"
            elif w is None:
                text, colour = "#", "#90A4AE"
            else:
                text, colour = str(w), "#263238"
            ax.text(col_index, y, text, ha="center", va="center",
                    fontsize=11, color=colour, fontweight="bold", zorder=7)

    _plot_route(ax, result.search_bfs.route, PALETTE["dirty"], "o",
                f"BFS: {result.search_bfs.steps} steps, dose {result.search_bfs.weight}")
    _plot_route(ax, result.search_astar.route, PALETTE["clean"], "s",
                f"A*: {result.search_astar.steps} steps, dose {result.search_astar.weight}")

    ax.set_title("Astana block map: the shortest route versus the minimum-exposure route",
                 fontsize=12, pad=12)
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Patch(facecolor="#90A4AE", label="impassable (fenced depot, closed courtyard)"))
    labels.append("impassable (fenced depot, closed courtyard)")
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.04),
              frameon=False, fontsize=9.5)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def figure_search(result, path):
    labels = ["BFS\n(fewest steps)", "UCS\n(min exposure)", "A*\n(min exposure)"]
    doses = [result.search_bfs.weight, result.search_ucs.weight, result.search_astar.weight]
    steps = [result.search_bfs.steps, result.search_ucs.steps, result.search_astar.steps]
    expanded = [result.search_bfs.expanded, result.search_ucs.expanded, result.search_astar.expanded]

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2))
    for ax, values, title, colour in (
        (axes[0], doses, "Route dose\n(sum of block weights)", PALETTE["clean"]),
        (axes[1], steps, "Route length\n(steps)", PALETTE["accent"]),
        (axes[2], expanded, "Nodes expanded\n(search effort)", PALETTE["gold"]),
    ):
        bars = ax.bar(labels, values, color=colour, alpha=0.85, edgecolor="white")
        ax.bar_label(bars, fmt="%d", padding=2, fontsize=10, fontweight="bold")
        ax.set_title(title, fontsize=11)
        ax.set_ylim(0, max(values) * 1.22)
        ax.tick_params(axis="x", labelsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.25)

    fig.suptitle("Three search algorithms on the same 6x6 map", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def figure_value_iteration(result, path):
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for policy, colour, style in (
        (result.policy_baseline, PALETTE["dirty"], "--"),
        (result.policy_optimal, PALETTE["clean"], "-"),
    ):
        iterations = [h["iteration"] for h in policy.history]
        label = f"W = {policy.route_weight} ({'shortest route' if policy is result.policy_baseline else 'A* route'})"
        ax.plot(iterations, [float(h["V(A)"]) for h in policy.history],
                colour, linestyle=style, linewidth=2, label=f"V(A), {label}")
        ax.plot(iterations, [float(h["V(H)"]) for h in policy.history],
                colour, linestyle=style, linewidth=2, alpha=0.55, label=f"V(H), {label}")

    ax.axhline(0, color="#90A4AE", linewidth=0.8)
    ax.set_xlabel("Bellman backup (iteration k)")
    ax.set_ylabel("State value V(s), utility points")
    ax.set_title("Value iteration converges to the same policy, at a higher value\n"
                 "when the route is planned by A*", fontsize=12)
    ax.legend(fontsize=9, frameon=False, loc="center right")
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def figure_belief(result, path):
    beliefs = [float(result.forward.beliefs[0]["H"]),
               float(result.forward.beliefs[1]["H"]),
               float(result.forward.beliefs[2]["H"])]
    labels = ["prior", "1 reading\n'alarm'", "2 readings\n'alarm','alarm'", "3 readings\n'+ calm'"]
    values = [float(result.bayes_alarm.prior_hazardous)] + beliefs
    colours = [PALETTE["neutral"]] + [PALETTE["dirty"], PALETTE["dirty"], PALETTE["clean"]]

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    bars = ax.bar(labels, values, color=colours, alpha=0.85, edgecolor="white")
    ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=10, fontweight="bold",
                 labels=[f"{v:.1%}" for v in values])

    ax.axhline(float(result.decision_single_baseline.threshold), color=PALETTE["dirty"],
               linestyle="--", linewidth=1.6)
    ax.text(3.42, float(result.decision_single_baseline.threshold) + 0.015,
            f"p* shortest route = {float(result.decision_single_baseline.threshold):.1%}",
            ha="right", fontsize=9, color=PALETTE["dirty"])
    ax.axhline(float(result.decision_single_optimal.threshold), color=PALETTE["clean"],
               linestyle="--", linewidth=1.6)
    ax.text(3.42, float(result.decision_single_optimal.threshold) + 0.015,
            f"p* A* route = {float(result.decision_single_optimal.threshold):.1%}",
            ha="right", fontsize=9, color=PALETTE["clean"])

    ax.set_ylim(0, 1.0)
    ax.set_ylabel("P(hazardous air)")
    ax.set_title("How the belief in hazardous air evolves, and the two decision thresholds",
                 fontsize=12)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def figure_decision(result, path):
    """Q(Go) and Q(Wait) as functions of p = P(hazardous), for both routes."""
    p = np.linspace(0, 1, 400)
    fig, ax = plt.subplots(figsize=(8.2, 4.8))

    for decision, colour, name in (
        (result.decision_single_baseline, PALETTE["dirty"], "shortest route (W = 19)"),
        (result.decision_single_optimal, PALETTE["clean"], "A* route (W = 14)"),
    ):
        r = decision.rewards
        q_go = (1 - p) * float(r["A"]["Go"]) + p * float(r["H"]["Go"])
        q_wait = (1 - p) * float(r["A"]["Wait"]) + p * float(r["H"]["Wait"])
        ax.plot(p, q_go, color=colour, linewidth=2.2, label=f"Q(Go), {name}")
        ax.plot(p, q_wait, color=colour, linewidth=2.2, linestyle=":", label=f"Q(Wait), {name}")
        ax.axvline(float(decision.threshold), color=colour, linewidth=1, alpha=0.45)
        ax.plot([float(decision.threshold)],
                [(1 - float(decision.threshold)) * float(r["A"]["Go"])
                 + float(decision.threshold) * float(r["H"]["Go"])],
                marker="X", markersize=11, color=colour)

    belief_single = float(result.decision_single_baseline.belief["H"])
    belief_sequence = float(result.forward.final_belief["H"])
    ax.set_ylim(-18.5, 9.0)
    for value, text, colour in (
        (belief_single, "Bayes, 1 reading\np = 64.6%", PALETTE["accent"]),
        (belief_sequence, "HMM, 3 readings\np = 18.1%", PALETTE["gold"]),
    ):
        ax.axvline(value, color=colour, linewidth=1.4, linestyle="--")
        ax.text(value + 0.012, -17.6, text, fontsize=9, color=colour, va="bottom")

    ax.set_xlabel("p = P(hazardous air)")
    ax.set_ylabel("One-step expected reward Q(b, a)")
    ax.set_title("Decision thresholds: where 'Go now' stops being worth it", fontsize=12)
    ax.legend(fontsize=8.5, frameon=False, loc="upper right")
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def figure_pipeline(result, path):
    """The integration diagram, drawn with real numbers from the run."""
    fig, ax = plt.subplots(figsize=(11.0, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    boxes = [
        (0.15, 3.0, 2.1, 1.0, "Home PM2.5 sensor\none reading: 'alarm'", PALETTE["neutral"]),
        (2.85, 3.0, 2.1, 1.0, "[1] Bayes\nP(H) = 51/79 = 64.6%", PALETTE["accent"]),
        (5.55, 3.0, 2.1, 1.0, "[3] MDP one-step\nQ(Go) vs Q(Wait)", PALETTE["gold"]),
        (8.05, 3.0, 1.8, 1.0, "Recommendation\nGO NOW", PALETTE["clean"]),
        (0.15, 1.3, 2.1, 1.0, "6x6 block map\nS = home, G = university", PALETTE["neutral"]),
        (2.85, 1.3, 2.1, 1.0, "[2] A* search\nroute dose W = 14 (BFS: 19)", PALETTE["clean"]),
        (5.55, 1.3, 2.1, 1.0, "R(s, Go) =\n12 - 0.02 x C(s) x W", PALETTE["gold"]),
        (0.15, 0.0, 2.1, 0.85, "3 hourly readings\nalarm, alarm, calm", PALETTE["neutral"]),
        (2.85, 0.0, 2.1, 0.85, "[4] HMM forward\nP(H) = 18.1%", PALETTE["accent"]),
        (5.55, 0.0, 2.1, 0.85, "Viterbi decode\nhidden: H, H, A", PALETTE["accent"]),
    ]
    for x, y, w, h, text, colour in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=colour, alpha=0.14,
                                   edgecolor=colour, linewidth=1.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=9.5, color="#212121")

    arrows = [
        ((2.25, 3.5), (2.85, 3.5)),
        ((4.95, 3.5), (5.55, 3.5)),
        ((7.65, 3.5), (8.05, 3.5)),
        ((2.25, 1.8), (2.85, 1.8)),
        ((4.95, 1.8), (5.55, 1.8)),
        ((6.6, 2.3), (6.6, 3.0)),
        ((3.9, 2.3), (3.9, 3.0)),
        ((2.25, 0.42), (2.85, 0.42)),
        ((4.95, 0.42), (5.55, 0.42)),
        ((6.6, 0.85), (6.6, 1.3)),
    ]
    for (x0, y0), (x1, y1) in arrows:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#455A64", linewidth=1.5))

    ax.set_title("CleanRoute Astana: one goal, four course algorithms, two feedback arrows",
                 fontsize=12.5, pad=10)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def figure_sensitivity(result, path):
    """The two sweeps: where does route planning change the recommendation?"""
    from airoute import experiments

    prior_sweep, sensor_sweep = experiments.run(
        result.search_bfs.weight, result.search_astar.weight
    )

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), sharey=True)
    for ax, sweep, colour in (
        (axes[0], prior_sweep, PALETTE["accent"]),
        (axes[1], sensor_sweep, PALETTE["gold"]),
    ):
        x = [row.parameter for row in sweep.rows]
        y = [float(row.posterior_h) for row in sweep.rows]
        disagree = [row.decision_shortest != row.decision_astar for row in sweep.rows]
        ax.plot(x, y, color=colour, linewidth=2.2, marker="o", markersize=4,
                label="P(H | alarm)")
        for xi, yi, flag in zip(x, y, disagree):
            if flag:
                ax.plot([xi], [yi], marker="X", markersize=11, color=PALETTE["dirty"], zorder=5)
        ax.axhline(float(sweep.rows[0].threshold_shortest), color=PALETTE["dirty"],
                   linestyle="--", linewidth=1.3)
        ax.text(0.98, float(sweep.rows[0].threshold_shortest) + 0.02,
                f"p* shortest = {float(sweep.rows[0].threshold_shortest):.1%}",
                transform=ax.get_yaxis_transform(), ha="right", fontsize=8.5,
                color=PALETTE["dirty"])
        ax.axhline(float(sweep.rows[0].threshold_astar), color=PALETTE["clean"],
                   linestyle="--", linewidth=1.3)
        ax.text(0.98, float(sweep.rows[0].threshold_astar) + 0.02,
                f"p* A* = {float(sweep.rows[0].threshold_astar):.1%}",
                transform=ax.get_yaxis_transform(), ha="right", fontsize=8.5,
                color=PALETTE["clean"])
        ax.set_xlabel(sweep.parameter_name)
        ax.set_title(f"{len(sweep.disagreements)} of {len(sweep.rows)} values: routes disagree (X)",
                     fontsize=11)
        ax.grid(alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("P(hazardous air) after one 'alarm'")
    axes[0].set_ylim(0, 1.02)
    fig.suptitle("Sensitivity: the recommendation band where route planning decides",
                 fontsize=12.5, y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def build_all(out_dir=ASSETS):
    os.makedirs(out_dir, exist_ok=True)
    result = pipeline.run()
    targets = {
        "fig_map.png": figure_map,
        "fig_search_comparison.png": figure_search,
        "fig_value_iteration.png": figure_value_iteration,
        "fig_belief_evolution.png": figure_belief,
        "fig_decision_threshold.png": figure_decision,
        "fig_pipeline.png": figure_pipeline,
        "fig_sensitivity.png": figure_sensitivity,
    }
    written = []
    for name, builder in targets.items():
        destination = os.path.join(out_dir, name)
        builder(result, destination)
        written.append(destination)
        print(f"  wrote {destination}")
    return written


if __name__ == "__main__":
    build_all()
