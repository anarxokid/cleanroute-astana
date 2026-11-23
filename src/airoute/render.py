"""Console rendering: the map, the tables and the step traces.

Kept separate from the algorithms so that the algorithm modules stay pure and
testable, and so the same result objects can be reused by the notebook and by
the figure generator.
"""

from airoute.scenario import GOAL, GRID, START

WIDTH = 78

def rule(char="-"):
    print(char * WIDTH)


def section(number, title):
    print()
    rule("=")
    print(f"  PART {number} - {title}")
    rule("=")


def subtitle(text):
    print()
    print(f"--- {text} " + "-" * max(0, WIDTH - len(text) - 5))


def steps(trace):
    for line in trace:
        print(line)


def table(headers, rows, aligns=None):
    """A fixed-width text table; ``aligns`` is a string like 'lrrr'."""
    headers = [str(h) for h in headers]
    rows = [[str(cell) for cell in row] for row in rows]
    aligns = aligns or "l" * len(headers)

    widths = [
        max(len(headers[c]), *(len(r[c]) for r in rows)) if rows else len(headers[c])
        for c in range(len(headers))
    ]

    def fmt(cells):
        out = []
        for c, cell in enumerate(cells):
            out.append(cell.rjust(widths[c]) if aligns[c] == "r" else cell.ljust(widths[c]))
        return "  ".join(out).rstrip()

    print(fmt(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt(row))


def render_grid(route=None, marks=None):
    """Draw the 6x6 map. ``route`` cells are shown in brackets."""
    route = set(route or [])
    marks = marks or {}

    header = "        " + "".join(f"col {c}".rjust(8) for c in range(len(GRID[0])))
    print(header)
    for row_index, row in enumerate(GRID):
        cells = []
        for col_index, w in enumerate(row):
            cell = (row_index, col_index)
            if cell == START:
                base = "S"
            elif cell == GOAL:
                base = "G"
            elif w is None:
                base = "#"
            else:
                base = str(w)
            base = marks.get(cell, base)
            cells.append(f"[{base}]".rjust(8) if cell in route else base.rjust(8))
        print(f"row {row_index}  " + "".join(cells))

    print()
    print("  legend:  S = home, G = university, # = impassable (fenced depot,")
    print("           closed courtyards), 1..5 = relative PM2.5 weight of the block")
    print("           (1 = park, 5 = busy avenue), [x] = cell on the drawn route")


def route_line(route):
    return " -> ".join(f"{cell}" for cell in route)


def route_weights(route):
    return " + ".join(str(GRID[r][c]) for r, c in route)


def summary(label, text):
    print()
    print(f"  {label}: {text}")
