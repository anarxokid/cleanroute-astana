"""Local web interface: ``python -m airoute.web``.

Serves one page on 127.0.0.1 and recomputes the recommendation with the same
four algorithms the console demo uses. No third-party packages are needed.
"""

import argparse
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from airoute import bayes, hmm, mdp, search
from airoute.scenario import ACTION_NAMES, GOAL, GRID, PRIOR_HAZARDOUS, START

PAGE = Path(__file__).with_name("web_page.html").read_text(encoding="utf-8")

ROUTES = {
    "shortest": ("shortest-distance route", search.bfs),
    "astar": ("minimum-exposure route", search.astar),
}


def advise_payload(readings, route_key):
    """Everything the page needs for one recommendation."""
    if not 1 <= len(readings) <= 3:
        raise ValueError("one to three readings are required")
    for reading in readings:
        if reading not in ("alarm", "calm"):
            raise ValueError(f"unknown sensor signal: {reading!r}")
    if route_key not in ROUTES:
        raise ValueError(f"unknown route: {route_key!r}")

    found = {key: (name, find()) for key, (name, find) in ROUTES.items()}
    route_name, route = found[route_key]

    single = bayes.update(readings[0]) if len(readings) == 1 else None
    forward = hmm.forward(readings) if len(readings) > 1 else None
    viterbi = hmm.viterbi(readings) if len(readings) > 1 else None

    beliefs = [single.belief] if single else forward.beliefs
    decision = mdp.decide(beliefs[-1], route.weight, route_name)

    return {
        "readings": list(readings),
        "prior": float(PRIOR_HAZARDOUS),
        "beliefs_h": [float(belief["H"]) for belief in beliefs],
        "viterbi": viterbi.sequence if viterbi else None,
        "route": {
            "key": route_key,
            "name": route_name,
            "steps": route.steps,
            "weight": route.weight,
            "cells": [list(cell) for cell in route.route],
        },
        "routes": {
            key: {"name": name, "steps": result.steps, "weight": result.weight}
            for key, (name, result) in found.items()
        },
        "decision": {
            "action": decision.action,
            "action_label": ACTION_NAMES[decision.action],
            "belief_h": float(decision.belief["H"]),
            "q_go": float(decision.q_values["Go"]),
            "q_wait": float(decision.q_values["Wait"]),
            "threshold": float(decision.threshold),
            "margin": float(
                decision.q_values[decision.action] - min(decision.q_values.values())
            ),
        },
        "grid": [[w for w in row] for row in GRID],
        "start": list(START),
        "goal": list(GOAL),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(200, "text/html; charset=utf-8", PAGE.encode("utf-8"))
            return
        if parsed.path == "/api/advise":
            query = parse_qs(parsed.query)
            readings = tuple(
                item for item in query.get("readings", ["alarm"])[0].split(",") if item
            )
            route_key = query.get("route", ["astar"])[0]
            try:
                payload = advise_payload(readings, route_key)
            except ValueError as error:
                body = json.dumps({"error": str(error)}).encode("utf-8")
                self._send(400, "application/json; charset=utf-8", body)
                return
            body = json.dumps(payload).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)
            return
        self._send(404, "text/plain; charset=utf-8", b"not found")

    def _send(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m airoute.web",
        description="CleanRoute Astana - local web adviser.",
    )
    parser.add_argument("--port", type=int, default=8000, help="port to listen on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser")
    args = parser.parse_args(argv)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"  CleanRoute Astana web adviser: {url}")
    print("  press Ctrl+C to stop")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
