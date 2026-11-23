# PROGRESS — CleanRoute Astana (Final Project, AI Fundamentals)

Living work journal. Update after every meaningful step so the project can be
resumed after an interruption without losing context.

- **Student:** Ibragim Mukash
- **Course:** AI Fundamentals, Final Project
- **Package:** `src/airoute`, version 1.1.0
- **Last updated:** 2026-11-23

---

## Stage 1 — Study the assignment (DONE)

- Opened the assignment page on Qairu Campus through the user's already-signed-in
  Chrome tab (no credentials requested, no auth bypass).
- Downloaded and read the two official attachments into `documentation/`:
  - `Final_Project_assignment.docx` — objective (integrate ≥3 algorithms from
    different topics toward a common goal), deliverables (working prototype, source
    code + brief documentation, live demo + oral defence with Q&A), 5 evaluation
    criteria, teamwork ≤4, and the explicit warning that *three unrelated algorithms
    are not enough*.
  - `MiniAI_FPTopics.docx` — detailed guidelines: three parts may be separate
    mini-demos; small predefined inputs allowed; per algorithm show
    input → calculation → output → one-sentence explanation; submission = Python
    code/notebook + short README with sample I/O + brief live demo; console output
    sufficient; 20 example topics or an original idea.
- Also downloaded the student's own graded `Practice_8.ipynb` as a style reference
  (English, exact `Fraction` arithmetic, formula→substitution→result, pandas answer
  tables, "Interpretation"/"Conclusion" sections).
- **Reported to the user:** requirements, goal, expected result, technologies, files,
  criteria, mandatory elements, workload, risks (see conversation).

## Stage 2 — Concept (DONE)

- Chose an **original** topic (not one of the 20 examples) that is locally meaningful
  (Astana winter smog, coal-heating season) and satisfies the "common goal" rule by construction:
  *Bayes → belief*, *A\* → route dose*, *MDP → Go/Wait*, *HMM → better belief*.
- Rejected the 20 template topics as less original; rejected anything needing a real
  dataset or trained model (guidelines explicitly allow predefined inputs).

## Stage 3 — Research / inputs (DONE)

- All probabilities, transitions, rewards and the map are **hypothetical and labelled**
  in `src/airoute/scenario.py` (single source of truth). No fabricated datasets,
  experiments or citations: the only references are the course notes and AIMA.

## Stage 4 — Implementation (DONE)

- `src/airoute/` package: `scenario`, `bayes`, `search`, `mdp`, `hmm`, `pipeline`,
  `experiments`, `figures`, `render`, `cli`, `__main__`.
- Exact arithmetic via `fractions.Fraction` everywhere a probability/threshold is
  derived; floats only for plotting.
- Verified integration claims numerically:
  - BFS shortest = 8 steps / weight 19; UCS & A\* = 12 steps / weight 14 (−26.3% dose);
    A\* expands 16 nodes vs UCS 21 vs BFS 27.
  - One reading `alarm` → `P(H)=51/79≈64.6%`; shortest route `p*=49.5%`→Wait, A\* route
    `p*=79.7%`→Go (decision flips purely from route planning).
  - Value iteration (γ=0.9): V rises from (6.30, −8.11) to (7.80, −6.94); policy Go/Wait.
  - HMM over (alarm, alarm, calm): Viterbi `['H','H','A']`; forward belief 64.6% →
    80.6% → 18.1%, which flips the final recommendation to Go on both routes.

## Stage 5 — Deliverables (DONE)

- `README.md` (with real sample I/O), `requirements.txt`, `results/*`
  (demo_output.txt, demo_output_verbose.txt, results.json, sweep_prior.csv,
  sweep_sensor.csv), `assets/` 7 figures.
- `Final_Project_CleanRoute_Astana.ipynb` — self-contained, executed, 22 cells,
  1 figure, 0 errors; numbers match the package exactly (27/21/16 expansions).
- `reports/Final_Project_report.docx` — 8 sections, 6 tables, 7 embedded figures.
- `presentation/Final_Project_presentation.pptx` — 16 slides, geometry verified
  (no overlaps, nothing out of bounds).
- `documentation/Defense_prep_RU.md` — defence notes in Russian (11 points, code
  walkthrough, speech, Q&A incl. hard questions, demo scenario).

## Stage 6 — Testing (DONE)

- `tests/test_airoute.py`: **26 tests, all passing** (`py -m pytest tests -q` and
  standalone `py tests/test_airoute.py`).
- CLI verified end-to-end: every `--section` value, `--verbose`, `--json`,
  `--no-header` exit 0; invalid `--section` exits 2; `bayes.update('bogus')`
  raises ValueError.
- Dependency check: core algorithms are stdlib-only (matplotlib/numpy only in
  `figures.py`); installed versions satisfy `requirements.txt`
  (matplotlib 3.11.2, numpy 2.5.4, pandas 3.1.0, pytest 9.2.0, Python 3.14.7).

## Stage 7 — Defence preparation (DONE)

- `documentation/Defense_prep_RU.md`: problem, topic choice, pipeline, technologies,
  each algorithm in plain language with the real numbers, data provenance, sequential
  code walkthrough with line references, input→result path, limitations, future work,
  a 2–3 minute speech, a live demo script, and teacher Q&A (normal + advanced).

## Stage 8 — Final rubric audit (DONE)

See the audit table at the end of this file. Nothing is submitted to Qairu Campus;
the final go-ahead stays with the student.

## Errors found & fixed (selected)

- cp1251 `UnicodeEncodeError` on `→` → run with `PYTHONIOENCODING=utf-8`.
- `part_summary()` missing `verbose` kwarg → added.
- Viterbi backtrace print was wrong → rewrote as `psi_{t+1}(state) -> predecessor`.
- `figure_map` drew two legends and hid cell text behind route markers → single
  combined legend, text `zorder=7`.
- `figure_decision` belief labels overlapped the title → explicit `ylim` + low labels.
- HMM transition print `P(A|A)` was ambiguous → arrow notation `P(A->A)`.
- Results-table numbering didn't match print order → renumbered 1…4d/FINAL.
- Earlier hand-computed Viterbi `['H','A','A']` was wrong (wrong emission at t=2);
  code's `['H','H','A']` confirmed by re-derivation.
- Section numbering: experiments was labelled PART 6 while printing before the
  PART 5 summary → experiments is now PART 5, integration/results PART 6.

## Decisions log

- Language of deliverables: **English** (assignment, guidelines, lectures and the
  student's past submissions are all English). Chat + defence-prep notes: Russian.
- Submission pattern follows the student's proven habit: `.ipynb` + console output.
- Do **not** submit to the platform without the user's explicit go-ahead.

---

# FINAL RUBRIC AUDIT (Stage 8)

Verbatim criteria from `documentation/Final_Project_assignment.docx` and
`documentation/MiniAI_FPTopics.docx`. Status: **Done** / **Partial** / **Not done**.

## A. Evaluation Criteria (the 5 graded criteria)

| # | Teacher criterion (verbatim) | Required result | What is implemented | Status |
|---|---|---|---|---|
| A1 | Correct implementation and integration of at least three AI algorithms. | ≥3 algorithms from different topics, correctly implemented **and** integrated | 4 algorithms: Bayes (M6), BFS/UCS/A* (M2–4), MDP (M5), HMM (M7). Two functional hand-offs: route weight → MDP reward; HMM filtered belief → MDP decision; each flips the recommendation. 26 tests pin every exact value | Done |
| A2 | Project functionality and quality of results. | Working prototype; results demonstrated and evaluated | CLI runs end-to-end (all sections exit 0); executed notebook; 7 generated figures; sensitivity sweeps + CSVs; results.json; evaluation = sweeps + value-iteration confirmation | Done |
| A3 | Creativity and practical relevance. | Creative, real-world-relevant idea | Original topic (not among the 20 examples): Astana winter-smog travel adviser; locally meaningful; practical decision support | Done |
| A4 | Understanding of the implemented algorithms. | Student explains each algorithm, why chosen, how it contributes; answers questions | Per-algorithm INPUT→KEY CALCULATION→OUTPUT→EXPLANATION in console, notebook and report; `documentation/Defense_prep_RU.md` with speech, Q&A and advanced Q&A; code walkthrough with line references | Done (live performance is the student's) |
| A5 | Quality of the demonstration and oral defense. | Live demo + oral defence with Q&A | 16-slide deck, report, verified demo script (`Defense_prep_RU.md` §Demo); all demo commands re-run successfully | Done (demo performed live by student) |

## B. Project Requirements

| # | Requirement (verbatim) | What is implemented | Status |
|---|---|---|---|
| B1 | Project Idea: real-world problem + AI-based solution | Smog-aware leave/route decision; AI = 4 course algorithms | Done |
| B2 | Algorithms: ≥3 different topics, work together | 4 topics; integration proven by decision flips | Done |
| B3 | Implementation: working application/prototype/simulation | Console prototype + self-contained notebook | Done |
| B4 | Explanation: how each works, why selected, contribution | explain() per module + report §3 + defence notes §5 | Done |
| B5 | Results: demonstrate, evaluate, discuss improvements | demo output, sweeps (evaluation), report §7 + notebook Conclusion (improvements) | Done |
| B6 | Teamwork: individual or ≤4, all contribute | Individual work by Ibragim Mukash | Done |
| B7 | Future Development: expandable project | Report §7 / notebook Conclusion: calibration, Q-learning, deadline MDP, API | Done |

## C. Expected Deliverables

| # | Deliverable (verbatim) | What is implemented | Status |
|---|---|---|---|
| C1 | A working AI application, prototype, or simulation | `src/airoute` CLI + notebook | Done |
| C2 | Source code and brief project documentation | `src/`, `tests/`, `README.md`, `reports/Final_Project_report.docx` | Done |
| C3 | A live demonstration and oral defense, including Q&A | Demo script + deck + defence notes; to be performed by student | Done (prepared) |

## D. Guidelines checklist (MiniAI_FPTopics)

| # | Checklist item | What is implemented | Status |
|---|---|---|---|
| D1 | Three algorithms, one from each stated group | search + Bayes + MDP (plus HMM as a labelled fourth) | Done |
| D2 | Inputs, assumptions, intermediate steps, outputs visible | Console prints INPUT/KEY CALCULATION/OUTPUT per case; assumptions block in header; exact fractions | Done |
| D3 | Can explain why each algorithm fits its subproblem | One-sentence EXPLANATION per algorithm + report + defence notes | Done |
| D4 | Working demonstration and at least one test case | 26 tests; full console demo saved | Done |
| D5 | Scope remains small; UI polish not required | 6×6 map, 2 states, 2 actions, 3 readings; console UI | Done |
| D6 | Submission: Python code/notebook + short README with sample I/O + brief live demo | `.ipynb` + package; README with real sample output; demo script | Done |

## E. Residual risks (honest)

- A4/A5/C3 depend on the student's live performance; mitigated by the defence notes
  and rehearsed speech, but not something code can guarantee.
- All inputs are hypothetical — explicitly permitted by the guidelines, and labelled
  everywhere; not a rubric risk, but must be stated aloud at the defence.
- Submission to Qairu Campus is intentionally **not** performed; awaiting the
  student's explicit approval.

## F. Submission package v1.1.0 (23 November 2026, DONE)

- Re-read the current assignment page: the required package is working app + local
  demo, source code + documentation, technical report, 5–7 slides, 2–3 minute video,
  AI Usage Declaration, Team Contribution Statement; defence 2 + 3–5 + 2 + ≤3 min.
- Version bumped to 1.1.0 (`src/airoute/__init__.py`, README); demo outputs regenerated;
  `python -m pytest tests -q` → 26 passed.
- Report updated: cover, submission-package line, §8 AI disclosure paragraph,
  Appendix A (compliance matrix), Appendix B (team contribution), Appendix C (AI-assisted
  development).
- Deck rebuilt as **7 slides** (`presentation/Final_Project_presentation.pptx`).
- Demo video built with Pillow + edge-tts + ffmpeg (`scripts/make_video.py`):
  1280×720, 15 fps, 2 min 35 s, narrated, real figures and a real console excerpt;
  narration disclosed as AI-generated (edge-tts) in the declaration.
- Declarations written (`docs/AI_Usage_Declaration.docx`,
  `docs/Team_Contribution_Statement.docx`).
- Local git repository initialised with `.gitignore`; publishing to GitHub is left to
  the student because it requires their own account and explicit consent.

