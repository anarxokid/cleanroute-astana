import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

PATH = "reports/Final_Project_report.docx"
d = docx.Document(PATH)

d.paragraphs[5].runs[0].text = "Package: src/airoute, version 1.1.0"
d.paragraphs[6].runs[0].text = "Date: 23 November 2026"

anchor = d.paragraphs[8]
pkg = anchor.insert_paragraph_before()
pkg.alignment = WD_ALIGN_PARAGRAPH.CENTER
pkg.paragraph_format.space_after = Pt(6)
run = pkg.add_run(
    "Submission package: this report \u00b7 7-slide deck \u00b7 2\u20133 minute demo video \u00b7 "
    "AI Usage Declaration \u00b7 Team Contribution Statement \u00b7 GitHub repository"
)
run.font.size = Pt(10)

sec8 = d.paragraphs[70]
sec8.add_run(
    " The formal declaration submitted with the project (docs/AI_Usage_Declaration.docx) lists each "
    "tool, the scope of its use and how its output was verified. The narration voice of the demo video "
    "is synthesised with edge-tts; the visuals are the real console output and the project's own figures."
)

d.add_page_break()

d.add_heading("Appendix A \u2014 Deliverables and compliance checklist", level=1)
d.add_paragraph(
    "The table maps every requirement of the assignment brief to the artefact that satisfies it. "
    "All artefacts are contained in the project repository."
)

rows = [
    ("Requirement", "Where it is delivered"),
    ("Working application with a local demo",
     "Console application src/airoute (python -m airoute); the full input \u2192 calculation \u2192 output trace is saved in results/demo_output.txt"),
    ("Public GitHub repository with the complete source",
     "The whole project is under git version control; the public repository link is given in the submission form"),
    ("Technical report",
     "reports/Final_Project_report.docx (this document)"),
    ("Presentation of 5\u20137 slides",
     "presentation/Final_Project_presentation.pptx \u2014 7 slides"),
    ("Demo video of 2\u20133 minutes",
     "demo/demo_video.mp4 \u2014 narrated walkthrough of the running code, the figures and the final recommendation"),
    ("At least three course algorithms integrated toward one goal",
     "Four algorithms: Bayesian inference (Section 3.1), BFS/UCS/A* search (3.2), MDP with value iteration (3.3) and HMM with Viterbi/forward filtering (3.4), joined by one pipeline (Section 5)"),
    ("AI Usage Declaration",
     "docs/AI_Usage_Declaration.docx"),
    ("Team Contribution Statement",
     "docs/Team_Contribution_Statement.docx"),
]
table = d.add_table(rows=len(rows), cols=2)
table.style = "Light Grid Accent 1"
for i, (left, right) in enumerate(rows):
    cells = table.rows[i].cells
    cells[0].text = left
    cells[1].text = right
    if i == 0:
        for c in cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.bold = True

d.add_heading("Appendix B \u2014 Team contribution", level=1)
d.add_paragraph(
    "The project was completed individually; there are no other team members. The student, Ibragim Mukash, "
    "is responsible for 100% of the work: the scenario and all hypothetical inputs, the four algorithm "
    "implementations, the integration pipeline, sensitivity experiments, figures, console application, "
    "notebook, automated tests, report, presentation, demo video and declarations. The detailed component-by-component "
    "table with evidence paths is provided in docs/Team_Contribution_Statement.docx."
)

d.add_heading("Appendix C \u2014 AI-assisted development", level=1)
d.add_paragraph(
    "AI tools were used as permitted by the guidelines and are declared in detail in "
    "docs/AI_Usage_Declaration.docx: a Qoder AI coding agent for scaffolding, refactoring, tests, figures and "
    "drafting; a large language model chat assistant for explanations, wording and defence preparation; and "
    "edge-tts for the demo-video narration voice. Every reported value is computed with exact fractions.Fraction "
    "arithmetic and pinned by the 26 automated tests, and the student reproduced each of them by running the "
    "code and the test suite."
)

d.save(PATH)
print("report updated")
