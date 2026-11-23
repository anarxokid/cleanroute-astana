import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY = RGBColor(0x14, 0x2A, 0x4A)
TEAL = RGBColor(0x17, 0x8A, 0x7A)
GREY = RGBColor(0x55, 0x5F, 0x6B)


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def base_doc():
    d = Document()
    sec = d.sections[0]
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)
    st = d.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(11)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.12
    for name, size in (("Heading 1", 16), ("Heading 2", 13)):
        h = d.styles[name]
        h.font.name = "Calibri"
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = NAVY
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
    return d


def eyebrow(d, text):
    p = d.add_paragraph()
    r = p.add_run(text.upper())
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = TEAL
    p.paragraph_format.space_after = Pt(2)
    return p


def title(d, text, size=26):
    p = d.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p.paragraph_format.space_after = Pt(4)
    return p


def subtitle(d, text, size=12, color=GREY, italic=False):
    p = d.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.italic = italic
    return p


def para(d, text, bold_lead=None, size=11):
    p = d.add_paragraph()
    if bold_lead:
        r = p.add_run(bold_lead)
        r.font.bold = True
        r.font.size = Pt(size)
        r.font.color.rgb = NAVY
    r = p.add_run(text)
    r.font.size = Pt(size)
    return p


def table(d, header, rows, widths=None):
    t = d.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(c, "142A4A")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            r = p.add_run(val)
            r.font.size = Pt(9.5)
            p.paragraph_format.space_after = Pt(2)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    return t


def signature(d):
    d.add_paragraph()
    p = d.add_paragraph()
    r = p.add_run(
        "Student signature: ______________________________        Date: 23 November 2026"
    )
    r.font.size = Pt(10.5)
    r.font.color.rgb = NAVY


def ai_declaration(path):
    d = base_doc()
    eyebrow(d, "Qairu University · AI Fundamentals — Final Project")
    title(d, "AI Usage Declaration")
    subtitle(d, "CleanRoute Astana — a mini air-quality adviser for outdoor travel", 13, NAVY, False)
    subtitle(d, "Student: Ibragim Mukash · Individual project · 23 November 2026", 10.5, GREY)

    d.add_heading("1. Purpose of this declaration", level=1)
    para(
        d,
        "The project guidelines require any AI-assisted code to be explained and declared. "
        "This document lists every AI tool used in the project, describes the scope of that use, "
        "and states how each result was verified. The declaration is part of the submission and is "
        "consistent with Section 8 of the technical report.",
    )

    d.add_heading("2. Tools used and scope", level=1)
    table(
        d,
        ["Tool", "What it was used for", "How the output was verified"],
        [
            [
                "Qoder AI coding agent (agentic IDE assistant)",
                "Scaffolding and refactoring the Python package src/airoute; drafting the unit-test suite; "
                "generating the figures and the console demo; assisting with the technical report and the 7-slide deck.",
                "The student ran the full pipeline and the test suite (26 tests pass). Every reported value is "
                "asserted against an exact fractions.Fraction computation. The student reviewed the code and can "
                "explain each algorithm line by line.",
            ],
            [
                "Large language model chat assistant",
                "Explanations, English wording and editing, and preparation notes for the oral defence.",
                "No factual claim or number was accepted unless it was reproduced by the executed code. "
                "Final text was reviewed by the student.",
            ],
            [
                "edge-tts text-to-speech",
                "Narration audio for the 2–3 minute demo video.",
                "The visuals are the real console output and the figures generated by the project; only the voice "
                "is synthesised.",
            ],
        ],
        widths=[3.6, 6.4, 6.4],
    )

    d.add_heading("3. What the student verified personally", level=1)
    for item in [
        "Runs the console application: PYTHONPATH=src python -m airoute (full input → calculation → output trace).",
        "Runs the automated tests: python -m pytest tests -q → 26 passed.",
        "Checked the four exact results by hand: P(H|alarm) = 51/79, P(H|calm) = 9/121, "
        "thresholds p* = 103/208 and 59/74, Viterbi sequence H, H, A.",
        "Explains why Bayes updates a prior into a posterior, how A* uses an admissible Manhattan heuristic, "
        "how the MDP turns a belief and a route dose into a threshold, and how forward filtering and Viterbi work together.",
        "Can reproduce every number in the report, slides and video from the code in the repository.",
    ]:
        p = d.add_paragraph(item, style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        for r in p.runs:
            r.font.size = Pt(10.5)

    d.add_heading("4. Academic integrity statement", level=1)
    para(
        d,
        "The project is original work prepared for the AI Fundamentals final project. No external dataset, trained model, "
        "or third-party code was used: all inputs are the small hypothetical probabilities, transition tables, rewards and "
        "6×6 toy map declared in the report and in scenario.py. AI tools were used as described above and are declared here "
        "and in the technical report. The student takes full responsibility for the correctness, understanding and presentation "
        "of the submitted work.",
    )
    para(
        d,
        "The student confirms that every team member (for an individual project — the student) understands the project and can "
        "answer questions during the defence, including the individual Q&A part.",
    )
    signature(d)
    d.save(path)


def team_statement(path):
    d = base_doc()
    eyebrow(d, "Qairu University · AI Fundamentals — Final Project")
    title(d, "Team Contribution Statement")
    subtitle(d, "CleanRoute Astana — a mini air-quality adviser for outdoor travel", 13, NAVY, False)
    subtitle(d, "Student: Ibragim Mukash · Individual project · 23 November 2026", 10.5, GREY)

    d.add_heading("1. Team composition", level=1)
    para(
        d,
        "The project was completed individually. There were no other team members, and no part of the work was "
        "produced by another student. The assignment permits individual work or groups of up to four students; this "
        "submission is individual.",
    )

    d.add_heading("2. Contribution by component", level=1)
    table(
        d,
        ["Component", "Contributor", "Share", "Evidence"],
        [
            ["Problem statement, scenario and all hypothetical input values", "Ibragim Mukash", "100%", "src/airoute/scenario.py; Section 2 of the report"],
            ["Algorithm 1 — Bayesian inference", "Ibragim Mukash", "100%", "src/airoute/bayes.py; tests/test_airoute.py"],
            ["Algorithm 2 — BFS / UCS / A* search", "Ibragim Mukash", "100%", "src/airoute/search.py; tests/test_airoute.py"],
            ["Algorithm 3 — Markov decision process, value iteration", "Ibragim Mukash", "100%", "src/airoute/mdp.py; tests/test_airoute.py"],
            ["Algorithm 4 — HMM, Viterbi and forward filtering", "Ibragim Mukash", "100%", "src/airoute/hmm.py; tests/test_airoute.py"],
            ["Integration pipeline, sensitivity experiments, figures", "Ibragim Mukash", "100%", "src/airoute/pipeline.py, experiments.py, figures.py"],
            ["Console application, notebook and automated tests", "Ibragim Mukash", "100%", "src/airoute/cli.py; Final_Project_CleanRoute_Astana.ipynb; tests"],
            ["Technical report, 7-slide presentation, demo video, declarations", "Ibragim Mukash", "100%", "reports/, presentation/, demo/, docs/"],
        ],
        widths=[7.4, 2.6, 1.4, 5.2],
    )

    d.add_heading("3. Declaration", level=1)
    para(
        d,
        "I confirm that this is an individual project; the contribution table above is accurate; and all external "
        "assistance, including AI tools, is declared in the accompanying AI Usage Declaration and in Section 8 of the "
        "technical report.",
    )
    para(
        d,
        "I understand that each student must be able to explain the project and answer questions individually during the defence.",
    )
    signature(d)
    d.save(path)


if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    ai_declaration("docs/AI_Usage_Declaration.docx")
    team_statement("docs/Team_Contribution_Statement.docx")
    print("written declarations")
