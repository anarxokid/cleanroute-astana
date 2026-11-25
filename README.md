# CleanRoute Astana — a mini air-quality adviser for outdoor travel

**Final Project — AI Fundamentals** · Student: Ibragim Mukash · version 1.1.0

One small, fully working pipeline that combines **four** course algorithms around a
single real-world goal: on a smoggy Astana winter evening, should a resident **leave now or
wait**, and if leaving, **which way should they walk**?

| # | Algorithm | Course module | Subproblem it solves |
|---|-----------|---------------|----------------------|
| 1 | Bayesian inference | Module 6 — Probability & Bayesian networks | Noisy home PM2.5 reading → belief `P(hazardous)` |
| 2 | A* search (vs BFS / UCS) | Modules 2–4 — Problem solving & search | 6×6 city map → minimum-exposure walking route |
| 3 | Markov decision process | Module 5 — MDP & reinforcement learning | Belief + route dose → *Go* or *Wait* (one-step expected reward + value iteration) |
| 4 | Hidden Markov model (Viterbi + forward) | Module 7 — HMM | Sequence of readings → better belief + most likely hidden air states |

The four are **not** separate exercises: the A* route weight enters the MDP reward
table, and the HMM filtered belief replaces the single-reading posterior — each
hand-off changes the final recommendation (see *Integration* below).

---

## The scenario (all inputs are hypothetical, as the guidelines allow)

- Hidden air states: `A` = acceptable (PM2.5 ≤ 50 µg/m³), `H` = hazardous (> 100 µg/m³).
- Prior `P(H) = 3/10`; home sensor `P(alarm|H) = 17/20`, `P(alarm|A) = 1/5`.
- Hourly air-quality chain `P(A→A) = 0.7`, `P(H→H) = 0.6`.
- Reward model `R(s,Go) = 12 − 0.02 · C(s) · W(route)` with `C(A)=15`, `C(H)=75`;
  waiting costs `R(A,Wait) = −4`, `R(H,Wait) = −6`; discount `γ = 0.9`.
- 6×6 block map, weights 1 (park) … 5 (busy avenue), `#` = impassable; home `S=(5,2)`,
  university `G=(0,5)`.

**No real dataset and no trained model are used.** Every probability, transition and
reward is a labelled assumption, and all arithmetic is done in exact
`fractions.Fraction` so every printed number is reproducible.

---

## Deliverables (submission package)

| # | Deliverable | File |
|---|-------------|------|
| 1 | Working application + local demo | [`src/airoute/`](src/airoute/) — `python -m airoute` (console) or `python -m airoute.web` (browser UI) from `src/` |
| 2 | Source code and documentation | this repository; [`README.md`](README.md); [`tests/test_airoute.py`](tests/test_airoute.py) |
| 3 | Technical report (DOCX) | [`reports/Final_Project_report.docx`](reports/Final_Project_report.docx) |
| 4 | Presentation, 7 slides (PPTX) | [`presentation/Final_Project_presentation.pptx`](presentation/Final_Project_presentation.pptx) |
| 5 | Demo video, 2 min 35 s (MP4) | [`demo/demo_video.mp4`](demo/demo_video.mp4) |
| 6 | AI Usage Declaration (DOCX) | [`docs/AI_Usage_Declaration.docx`](docs/AI_Usage_Declaration.docx) |
| 7 | Team Contribution Statement (DOCX) | [`docs/Team_Contribution_Statement.docx`](docs/Team_Contribution_Statement.docx) |

Extras: a self-contained notebook [`Final_Project_CleanRoute_Astana.ipynb`](Final_Project_CleanRoute_Astana.ipynb),
defence notes in Russian ([`documentation/Defense_prep_RU.md`](documentation/Defense_prep_RU.md)),
and the scripts that produced the declarations, report appendices and video
([`scripts/`](scripts/)).

---

## Project layout

```
AI_FINAL_PROJECT/
├── src/airoute/          the package (pure Python, stdlib for the algorithms)
│   ├── scenario.py       single source of every hypothetical input
│   ├── bayes.py          algorithm 1 — exact Bayesian update
│   ├── search.py         algorithm 2 — BFS / UCS / A* on the weighted grid
│   ├── mdp.py            algorithm 3 — one-step expected reward + value iteration
│   ├── hmm.py            algorithm 4 — Viterbi decoding + forward filtering
│   ├── pipeline.py       wires the four algorithms into one system
│   ├── experiments.py    sensitivity sweeps (which assumptions change the answer)
│   ├── figures.py        matplotlib figures, generated from the real results
│   ├── render.py         console tables / grids / section headers
│   ├── interactive.py    --interactive: your own readings and route
│   ├── web.py            local web adviser (`python -m airoute.web`)
│   ├── web_page.html     the single page served by web.py
│   ├── cli.py            command-line entry point
│   └── __main__.py       `python -m airoute`
├── tests/                26 pytest tests (also runnable standalone)
├── results/              demo_output.txt, demo_output_verbose.txt, results.json,
│                         sweep_prior.csv, sweep_sensor.csv
├── assets/               7 PNG figures produced by figures.py
├── demo/                 demo_video.mp4 (2:35 narrated); preview/ — slide stills
├── docs/                 AI Usage Declaration, Team Contribution Statement
├── reports/              Final_Project_report.docx
├── presentation/         Final_Project_presentation.pptx (7 slides)
├── documentation/        assignment brief, topic guidelines, Defence_prep_RU.md
├── scripts/              make_declarations.py, update_report.py, make_video.py
├── Final_Project_CleanRoute_Astana.ipynb   self-contained notebook demo
├── requirements.txt
└── PROGRESS.md           work journal
```

---

## Requirements & install

Python **3.10+**. The algorithms themselves use only the standard library; the
figures and the notebook need matplotlib / pandas.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

`requirements.txt`:

```
matplotlib>=3.8
numpy>=1.26
pandas>=2.0
pytest>=8.0
```

Only needed if you want to rebuild the demo video from
[`scripts/make_video.py`](scripts/make_video.py):

```bash
pip install pillow edge-tts imageio-ffmpeg
```

---

## How to run

From the `src/` directory:

```bash
cd src
python -m airoute                      # full pipeline, console output
python -m airoute --interactive        # type your own readings and route, get the recommendation
python -m airoute --section mdp        # one part only: bayes|search|mdp|hmm|experiments|summary
python -m airoute --verbose            # adds per-node search traces and Bellman history
python -m airoute --json out.json      # machine-readable results
python -m airoute.figures              # regenerate the 7 figures into ../assets
python -m airoute.experiments          # print + save the two sensitivity sweeps
python -m airoute.web                  # local web UI at http://127.0.0.1:8000/
```

`python -m airoute.web` starts a standard-library HTTP server and opens the page in
the browser (`--port`, `--no-browser` are optional). The page lets you pick 1–3 hourly
readings and a route; every change recomputes the same pipeline through
`/api/advise` and shows the recommendation, the 6×6 map and the belief trail.

From the project root, run the tests:

```bash
python -m pytest tests -q              # 26 passed
python tests/test_airoute.py           # same suite without pytest
```

### Sample output (real, trimmed)

```
  PART 1 - BAYESIAN INFERENCE  (Module 6 - Probability and Bayesian Networks)
--- Case 1 - the sensor reports 'alarm' --------------------------------------
INPUT
  prior            P(H) = 3/10 = 0.3000
  sensor model     P(alarm | H) = 17/20 = 0.8500
                   P(alarm | A) = 1/5 = 0.2000
  observation      e = 'alarm'
KEY CALCULATION
  P(e, H) = 17/20 x 3/10 = 51/200      P(e, A) = 1/5 x 7/10 = 7/50
  P(e)    = 51/200 + 7/50 = 79/200
  P(H | e) = 51/200 / 79/200 = 51/79 = 0.6456 = 64.6%
OUTPUT
  posterior P(H | alarm) = 51/79 = 64.6%   (prior was 30.0%)

  PART 2 - A* SEARCH
2b. UCS, minimum exposure   12 steps, exposure weight 14, 21 nodes expanded
2c. A*, minimum exposure    12 steps, exposure weight 14, 16 nodes expanded
2d. Dose reduction by A*    5 weight units, -26.3%, for 4 extra steps

  PART 3 - MARKOV DECISION PROCESS
3.  MDP, one reading + shortest route  Q(Go) = -8.419, Q(Wait) = -5.291, p* = 49.5% -> Wait
3b. MDP, one reading + A* route        Q(Go) = -3.046, Q(Wait) = -5.291, p* = 79.7% -> Go

  PART 4 - HIDDEN MARKOV MODEL
4.  Viterbi, three readings   ['alarm','alarm','calm'] -> hidden sequence ['H','H','A']
4b. Forward filtering         P(H) after 1/2/3 readings = 64.6%, 80.6%, 18.1%

  FINAL RECOMMENDATION
  Go now, 12-step route through the park belt, P(H) = 18.1% < p* = 79.7%
```

The complete, untrimmed run is saved in [`results/demo_output.txt`](results/demo_output.txt)
(verbose variant: `results/demo_output_verbose.txt`; machine-readable: `results/results.json`).

---

## Why this is one project, not three

1. **Search feeds the MDP.** With the single reading `alarm` (`P(H)=64.6%`) the
   *shortest* route (weight 19) yields `p* = 49.5%` → **Wait**, while the A*
   minimum-exposure route (weight 14) yields `p* = 79.7%` → **Go**. Same belief,
   different route, opposite advice — the route is an *input* to the decision.
2. **HMM feeds the MDP.** Filtering the three readings `(alarm, alarm, calm)` drops
   `P(H)` to 18.1%, below both thresholds, so *Go* becomes safe on either route;
   Viterbi explains why: the hidden sequence was `H, H, A` — the air has just cleared.
3. **Value iteration confirms the one-step rule.** The Bellman fixed point gives the
   same stationary policy (Go in A, Wait in H) and quantifies the route benefit:
   `V(A)` rises from +6.30 to +7.80.
4. **Sensitivity sweeps** (`results/sweep_prior.csv`, `results/sweep_sensor.csv`) show
   the scenario prior 0.30 lies *inside* the disagreement band (0.20–0.45), i.e. the
   integration genuinely matters here rather than being decorative.

---

## Figures

All seven PNGs in `assets/` are generated by `python -m airoute.figures` from the
computed results — none are hand-drawn:

`fig_map.png` (map + BFS vs A* routes) · `fig_search_comparison.png` ·
`fig_value_iteration.png` · `fig_belief_evolution.png` · `fig_decision_threshold.png` ·
`fig_sensitivity.png` · `fig_pipeline.png` (integration diagram with the real numbers).

---

## AI-assisted code disclosure

The package was developed with an AI coding assistant. Every algorithm implementation
was checked against hand-derived exact values, and those checks live in
[`tests/test_airoute.py`](tests/test_airoute.py) (e.g. `P(H|alarm) = 51/79`,
`p* = 59/74`, Viterbi `['H','H','A']`, Bellman fixed point `V(A) = 39/5`). The student
can reproduce and explain each step; the defence notes in
[`documentation/Defense_prep_RU.md`](documentation/Defense_prep_RU.md) walk through the
code line by line. The full declaration is in
[`docs/AI_Usage_Declaration.docx`](docs/AI_Usage_Declaration.docx); the video narration
was synthesised with edge-tts and is disclosed there as well.

## References

- Course lecture notes, Modules 2–7 (search, MDP, Bayesian networks, HMM).
- Russell, S., Norvig, P. *Artificial Intelligence: A Modern Approach*, 4th ed. —
  chapters on search, probabilistic reasoning, MDPs and HMMs.
- Assignment brief and topic guidelines (see `documentation/`).
