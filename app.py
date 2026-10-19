"""
AI & ML Assessment App
- Students log in with name and roll number
- 30 questions, 1 mark each (30 marks)
- Each roll number can submit only ONCE; results saved to results.xlsx

Run:  streamlit run app.py
"""
import html
import os
import threading
import time
from datetime import datetime

import streamlit as st
import gspread

from questions import QUESTIONS, UNITS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(BASE_DIR, os.environ.get("RESULTS_FILE", "results.xlsx"))
PASS_PERCENT = 40
LETTERS = "ABCD"
TOTAL = len(QUESTIONS)
TEST_MINUTES = 30
TEST_SECONDS = TEST_MINUTES * 60

STATUS_IN_PROGRESS = "In progress"
STATUS_SUBMITTED = "Submitted"
STATUS_TIME_UP = "Time up"

FIXED_HEADERS = ["Timestamp", "Name", "Roll Number", "Status", "Score", "Total Marks",
                 "Percentage", "Time Taken (min)", "Started At"]
HEADERS = FIXED_HEADERS + [f"Q{i + 1} Answer" for i in range(TOTAL)]
COL_TIMESTAMP, COL_NAME, COL_ROLL, COL_STATUS = 1, 2, 3, 4
COL_SCORE, COL_TOTAL, COL_PCT, COL_MIN, COL_STARTED = 5, 6, 7, 8, 9
FIRST_ANSWER_COL = len(FIXED_HEADERS) + 1

_file_lock = threading.Lock()   # only one write at a time


class SaveError(Exception):
    """Raised when Google Sheets cannot be accessed or updated."""


@st.cache_resource
def _get_results_worksheet():
    """Connect to the Results worksheet using Streamlit secrets."""
    try:
        service_account_info = dict(st.secrets["gcp_service_account"])
        spreadsheet_url = st.secrets["spreadsheet_url"]
        client = gspread.service_account_from_dict(service_account_info)
        spreadsheet = client.open_by_url(spreadsheet_url)
        try:
            ws = spreadsheet.worksheet("Results")
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(
                title="Results",
                rows=max(1000, TOTAL + 10),
                cols=len(HEADERS)
            )

        existing_headers = ws.row_values(1)
        if not existing_headers:
            ws.update(range_name=f"A1:{gspread.utils.rowcol_to_a1(1, len(HEADERS))}",
                      values=[HEADERS])
            ws.freeze(rows=1)
            ws.format("A1:AM1", {
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "backgroundColor": {"red": 0.12, "green": 0.23, "blue": 0.54},
                "horizontalAlignment": "CENTER",
                "wrapStrategy": "WRAP"
            })
            ws.format("G2:G", {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}})
        elif existing_headers != HEADERS:
            raise SaveError(
                "The first row of the Google Sheets 'Results' tab does not match "
                "this app's expected columns. Rename the old tab as a backup, then "
                "create an empty tab named 'Results' and restart the app."
            )
        return ws
    except SaveError:
        raise
    except Exception as exc:
        raise SaveError(
            "Could not connect to Google Sheets. Check Streamlit secrets, the "
            "spreadsheet URL, and whether the service-account email has Editor access."
        ) from exc


def _all_rows(ws):
    return ws.get_all_values()


def _find_row(rows, roll):
    for row_num, row in enumerate(rows[1:], start=2):
        if len(row) >= COL_ROLL and str(row[COL_ROLL - 1] or "").strip().upper() == roll:
            return row_num
    return None


def ensure_results_file():
    """Confirm that the Google Sheets Results worksheet is accessible and initialized."""
    _get_results_worksheet()


def get_attempt(roll):
    """Return (status, started_at) for this roll number, or (None, None) if not seen."""
    try:
        ws = _get_results_worksheet()
        row_num = _find_row(_all_rows(ws), roll)
        if row_num is None:
            return None, None
        status = ws.cell(row_num, COL_STATUS).value
        started_raw = ws.cell(row_num, COL_STARTED).value
        started_at = None
        if started_raw:
            try:
                started_at = datetime.fromisoformat(started_raw)
            except (TypeError, ValueError):
                started_at = None
        return status, started_at
    except SaveError:
        raise
    except Exception as exc:
        raise SaveError("Could not read student attempts from Google Sheets.") from exc


def register_start(name, roll, started_at):
    """Record a student's start so a page reload cannot reset the timer."""
    with _file_lock:
        try:
            ws = _get_results_worksheet()
            rows = _all_rows(ws)
            if _find_row(rows, roll) is None:
                values = [
                    started_at.isoformat(timespec="seconds"), name, roll,
                    STATUS_IN_PROGRESS, "", TOTAL, "", "", started_at.isoformat(timespec="seconds")
                ] + [""] * TOTAL
                ws.append_row(values, value_input_option="RAW")
        except SaveError:
            raise
        except Exception as exc:
            raise SaveError("Could not record the student's start in Google Sheets.") from exc


def finalize(name, roll, score, minutes, answers, status) -> bool:
    """Write the final result. Returns False if the roll number was already finalized."""
    with _file_lock:
        try:
            ws = _get_results_worksheet()
            rows = _all_rows(ws)
            row_num = _find_row(rows, roll)
            if row_num is not None:
                current_status = ws.cell(row_num, COL_STATUS).value
                if current_status != STATUS_IN_PROGRESS:
                    return False
                started_at = ws.cell(row_num, COL_STARTED).value
                if row_num <= len(rows):
                    existing = rows[row_num - 1]
                    if len(existing) > COL_STARTED - 1 and existing[COL_STARTED - 1]:
                        started_at = existing[COL_STARTED - 1]
            else:
                row_num = len(rows) + 1
                started_at = datetime.now().isoformat(timespec="seconds")

            timestamp = datetime.now().isoformat(timespec="seconds")
            base_values = [
                timestamp, name, roll, status, score, TOTAL,
                score / TOTAL, minutes, started_at
            ] + list(answers)
            last_col = gspread.utils.rowcol_to_a1(1, len(HEADERS)).rstrip("1")
            ws.update(
                range_name=f"A{row_num}:{last_col}{row_num}",
                values=[base_values],
                value_input_option="RAW"
            )
            return True
        except SaveError:
            raise
        except Exception as exc:
            raise SaveError("Could not save the student's result to Google Sheets.") from exc


def generate_question_images():
    """Creates any missing question pictures inside the images/ folder."""
    needed = [q["image"] for q in QUESTIONS if q.get("image")]
    if all(os.path.exists(os.path.join(BASE_DIR, p)) for p in needed):
        return
    try:
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        from scipy.cluster.hierarchy import linkage, dendrogram
    except ImportError:
        return  # shown as a warning on the question card instead

    OUT = os.path.join(BASE_DIR, "images")
    os.makedirs(OUT, exist_ok=True)
    BLUE, PURPLE, CYAN, RED = "#2563eb", "#7c3aed", "#0891b2", "#e11d48"


    def save(fig, name):
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, name), dpi=130, facecolor="white")
        plt.close(fig)


    # 1. Histogram (Unit I: Matplotlib)
    rng = np.random.default_rng(7)
    data = rng.normal(50, 10, 300)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(data, bins=15, color=BLUE, edgecolor="white")
    ax.set_title("Distribution of Exam Scores")
    ax.set_xlabel("Score")
    ax.set_ylabel("Number of students")
    save(fig, "q_histogram.png")

    # 2. Box plot with one outlier (Unit II: EDA)
    values = [12, 14, 15, 15, 16, 17, 18, 19, 20, 21, 44]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot(values, vert=True, patch_artist=True,
               boxprops=dict(facecolor="#dbeafe", color=BLUE),
               medianprops=dict(color=RED, linewidth=2),
               whiskerprops=dict(color=BLUE), capprops=dict(color=BLUE),
               flierprops=dict(marker="o", markerfacecolor=RED, markeredgecolor=RED))
    ax.set_title("Box Plot of a Numeric Feature")
    ax.set_ylabel("Value")
    ax.set_xticks([])
    save(fig, "q_boxplot.png")

    # 3. Confusion matrix: TP=40, FP=10, FN=20, TN=30 (Unit III: metrics)
    cm = np.array([[40, 20], [10, 30]])   # rows = actual, cols = predicted
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.imshow(cm, cmap="Blues")
    labels = [["TP = 40", "FN = 20"], ["FP = 10", "TN = 30"]]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, labels[i][j], ha="center", va="center", fontsize=14,
                    color="white" if cm[i, j] > 25 else "#0f172a", fontweight="bold")
    ax.set_xticks([0, 1], ["Predicted +", "Predicted -"])
    ax.set_yticks([0, 1], ["Actual +", "Actual -"])
    ax.set_title("Confusion Matrix")
    save(fig, "q_confusion_matrix.png")

    # 4. Dendrogram of 5 points (Unit IV: hierarchical clustering)
    pts = np.array([[1.0, 1.0], [1.2, 1.1], [5.0, 5.0], [5.3, 5.2], [9.0, 1.0]])
    Z = linkage(pts, method="single")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    dendrogram(Z, labels=["A", "B", "C", "D", "E"], ax=ax, color_threshold=0,
               above_threshold_color=PURPLE)
    ax.set_title("Dendrogram (Hierarchical Clustering)")
    ax.set_ylabel("Distance")
    save(fig, "q_dendrogram.png")

    # 5. XOR data points (Unit V: perceptron limitation)
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.scatter([0, 1], [0, 1], s=260, color=BLUE, label="Class 0", edgecolor="white", zorder=3)
    ax.scatter([0, 1], [1, 0], s=260, color=RED, label="Class 1", edgecolor="white", zorder=3)
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(-0.5, 1.5)
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.grid(alpha=0.3)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)
    ax.set_title("Two-Class Data Points")
    save(fig, "q_xor.png")

    # 6. Multilayer perceptron diagram: 3 inputs, 1 hidden layer of 4, 2 outputs (Unit V)
    layers = [3, 4, 2]
    names = [["x1", "x2", "x3"], ["h1", "h2", "h3", "h4"], ["y1", "y2"]]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    xs = [1, 3, 5]
    pos = []
    for li, n in enumerate(layers):
        ys = np.linspace(0, 3, n) if n > 1 else [1.5]
        pos.append([(xs[li], y) for y in ys])
    for li in range(2):
        for x1, y1 in pos[li]:
            for x2, y2 in pos[li + 1]:
                ax.plot([x1, x2], [y1, y2], color="#94a3b8", lw=1, zorder=1)
    for li, layer in enumerate(pos):
        for k, (x, y) in enumerate(layer):
            color = [CYAN, PURPLE, BLUE][li]
            ax.scatter([x], [y], s=900, color=color, edgecolor="white", zorder=2)
            ax.text(x, y, names[li][k], ha="center", va="center", color="white", fontsize=10,
                    fontweight="bold")
    for x, t in zip(xs, ["Input layer", "Hidden layer", "Output layer"]):
        ax.text(x, -0.9, t, ha="center", fontsize=11, color="#0f172a")
    ax.set_xlim(0, 6)
    ax.set_ylim(-1.3, 3.5)
    ax.axis("off")
    ax.set_title("Multilayer Perceptron")
    save(fig, "q_mlp.png")

    # 7. Object detection: bounding boxes on a scene (Unit VI: computer vision)
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.set_facecolor("#e2e8f0")
    ax.add_patch(Rectangle((0.5, 0.4), 4.0, 3.0, color="#cbd5e1"))           # road-ish background
    ax.add_patch(Rectangle((0.9, 1.0), 1.3, 0.9, color="#f97316"))          # object 1
    ax.add_patch(Rectangle((3.0, 1.2), 1.1, 1.4, color="#22c55e"))          # object 2
    for (x, y, w, h, label, col) in [
        (0.8, 0.9, 1.7, 1.5, "car 0.94", "#2563eb"),
        (2.85, 1.0, 1.5, 1.8, "person 0.89", "#7c3aed"),
    ]:
        ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor=col, lw=3))
        ax.text(x, y + h + 0.1, label, color=col, fontsize=11, fontweight="bold")
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 4.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Scene with Detected Objects")
    save(fig, "q_object_detection.png")


# ---------- Look and feel ----------

def neural_network_svg() -> str:
    """Draws a small neural-network illustration (no external image needed)."""
    layers = [4, 6, 6, 3]
    width, height = 900, 200
    xs = [90 + i * (width - 180) / (len(layers) - 1) for i in range(len(layers))]
    nodes = []
    for li, count in enumerate(layers):
        ys = [25 + (height - 50) * (k + 0.5) / count for k in range(count)]
        nodes.append([(xs[li], y) for y in ys])

    lines, circles = [], []
    for li in range(len(layers) - 1):
        for x1, y1 in nodes[li]:
            for x2, y2 in nodes[li + 1]:
                lines.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                             f'stroke="rgba(255,255,255,0.30)" stroke-width="1.4"/>')
    for layer in nodes:
        for x, y in layer:
            circles.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="#7dd3fc" '
                           f'stroke="#ffffff" stroke-width="2"/>')
    body = "".join(lines) + "".join(circles)
    return (f'<svg viewBox="0 0 {width} {height}" width="100%" '
            f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


STYLE = """
<style>
.hero {
  background: linear-gradient(135deg, #1e3a8a 0%, #6d28d9 55%, #0891b2 100%);
  border-radius: 20px; padding: 26px 30px 14px 30px; color: #ffffff;
  box-shadow: 0 10px 30px rgba(30, 58, 138, 0.25); margin-bottom: 18px;
}
.hero h1 { color: #ffffff; margin: 0 0 4px 0; font-size: 2.1rem; }
.hero p { margin: 0 0 10px 0; opacity: 0.92; font-size: 1.02rem; }
.chips span {
  display: inline-block; background: rgba(255,255,255,0.18); border-radius: 999px;
  padding: 4px 12px; margin-right: 8px; font-size: 0.85rem;
}
.result-card {
  border-radius: 18px; padding: 22px; text-align: center; color: #ffffff;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15); margin: 12px 0;
}
.result-card .big { font-size: 3rem; font-weight: 700; margin: 6px 0; }
.result-pass { background: linear-gradient(135deg, #059669, #10b981); }
.result-fail { background: linear-gradient(135deg, #b91c1c, #f43f5e); }
.unit-banner {
  display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin:20px 0 8px 0;
  padding:12px 16px; border-radius:14px; color:#ffffff;
  background: linear-gradient(90deg, #1e3a8a, #6d28d9);
  box-shadow: 0 6px 16px rgba(30, 58, 138, 0.2);
}
.unit-tag, .co-tag {
  padding:3px 11px; border-radius:999px; background:rgba(255,255,255,0.22);
  font-weight:700; font-size:0.88rem;
}
.unit-title { font-weight:600; font-size:1.02rem; }
.q-head { display:flex; align-items:center; gap:12px; margin-bottom:6px; }
.q-badge {
  min-width:44px; height:44px; border-radius:12px; display:flex; align-items:center;
  justify-content:center; color:#fff; font-weight:700;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
}
.q-text { font-size:1.05rem; font-weight:600; line-height:1.4; }
.stButton > button[kind="primary"], .stFormSubmitButton > button {
  border-radius: 12px; font-weight: 600; padding: 0.55rem 1.4rem;
}
</style>
"""


def render_header(subtitle: str):
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown(
        '<div class="hero">'
        '<h1>🧠 AI &amp; ML Assessment</h1>'
        f'<p>{html.escape(subtitle)}</p>'
        f'{neural_network_svg()}'
        '<div class="chips">'
        f'<span>📝 {TOTAL} Questions</span>'
        f'<span>🎯 {TOTAL} Marks</span>'
        f'<span>✅ Pass: {PASS_PERCENT}%</span>'
        '<span>🔒 One attempt only</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------- Screens ----------

def login_screen():
    render_header("Log in with your name and roll number to begin.")

    message = st.session_state.pop("login_msg", None)
    if message:
        st.error(message)

    with st.container(border=True):
        st.subheader("🎓 Student Login")
        with st.form("login_form"):
            name = st.text_input("Full name", placeholder="e.g. Aarav Sharma")
            roll = st.text_input("Roll number", placeholder="e.g. 24AI001")
            submitted = st.form_submit_button("Start Test ➜", type="primary")

    if not submitted:
        return
    name = name.strip()
    roll = roll.strip().upper()
    if not name or not roll:
        st.error("Please enter both your name and roll number.")
        return

    try:
        status, started = get_attempt(roll)
        if status in (STATUS_SUBMITTED, STATUS_TIME_UP):
            st.error("This roll number has already taken the test. "
                     "Each roll number can attempt it only once.")
            return
        if status == STATUS_IN_PROGRESS:
            started_dt = started if isinstance(started, datetime) else datetime.now()
            if time.time() >= started_dt.timestamp() + TEST_SECONDS:
                finalize(name, roll, 0, TEST_MINUTES, ["-"] * TOTAL, STATUS_TIME_UP)
                st.error("Your test time has already ended, so the test was closed.")
                return
            resumed = True
        else:
            started_dt = datetime.now()
            register_start(name, roll, started_dt)
            resumed = False
    except SaveError as exc:
        st.error(str(exc))
        return

    st.session_state.stage = "quiz"
    st.session_state.name = name
    st.session_state.roll = roll
    st.session_state.start = started_dt.timestamp()
    st.session_state.deadline = started_dt.timestamp() + TEST_SECONDS
    st.session_state.resumed = resumed
    st.session_state.auto_submitted = False
    st.rerun()


def show_question_image(relative_path):
    path = os.path.join(BASE_DIR, relative_path)
    if os.path.exists(path):
        st.image(path, width=520)
    else:
        st.warning("This question's picture could not be created. "
                   "Install the packages: pip install matplotlib scipy numpy")


def time_left() -> int:
    return max(0, int(st.session_state.deadline - time.time()))


@st.fragment(run_every=1)
def timer_panel():
    """Countdown that refreshes every second and submits when time is up."""
    remaining = time_left()
    if remaining <= 0:
        finish_test(auto=True)
        return
    mins, secs = divmod(remaining, 60)
    color = "#e11d48" if remaining <= 300 else "#059669"   # red during the last 5 minutes
    st.markdown(
        f'<div style="text-align:center; padding:12px; border-radius:14px; '
        f'background:{color}; color:#fff; font-size:2rem; font-weight:700; '
        f'letter-spacing:2px;">⏱ {mins:02d}:{secs:02d}</div>',
        unsafe_allow_html=True,
    )
    st.progress(remaining / TEST_SECONDS)
    if remaining <= 300:
        st.caption("Less than 5 minutes left!")


def quiz_screen():
    if "deadline" not in st.session_state:
        st.session_state.deadline = st.session_state.start + TEST_SECONDS
    if time_left() <= 0:
        finish_test(auto=True)

    with st.sidebar:
        st.markdown(f"### 👤 {html.escape(st.session_state.name)}")
        st.caption(f"Roll No: {st.session_state.roll}")
        timer_panel()
        st.markdown("---")
        st.markdown(f"**Questions:** {TOTAL}  \n**Marks:** {TOTAL}  \n"
                    f"**Time limit:** {TEST_MINUTES} min  \n**Pass mark:** {PASS_PERCENT}%")
        st.markdown("---")
        st.markdown("**Rules**  \n• Answer every question  \n• One submission only  \n"
                    f"• Test submits automatically after {TEST_MINUTES} min")

    render_header(f"Welcome, {st.session_state.name} · Roll No. {st.session_state.roll}")
    if st.session_state.get("resumed"):
        st.warning("You are resuming an earlier attempt. The timer continues from the "
                   "original start time. Answers given before the page was reloaded "
                   "were not kept, so please answer again.")
    st.info(f"You have **{TEST_MINUTES} minutes**. Answer the questions, then press "
            "**Submit Test**. Your answers are submitted automatically when time runs out.")

    for i, q in enumerate(QUESTIONS):
        if i == 0 or q["unit"] != QUESTIONS[i - 1]["unit"]:
            code, co, title = UNITS[q["unit"]]
            st.markdown(
                f'<div class="unit-banner"><span class="unit-tag">{code}</span>'
                f'<span class="co-tag">{co}</span>'
                f'<span class="unit-title">{html.escape(title)}</span></div>',
                unsafe_allow_html=True,
            )
        with st.container(border=True):
            st.markdown(
                f'<div class="q-head"><div class="q-badge">{i + 1}</div>'
                f'<div class="q-text">{html.escape(q["q"])}</div></div>',
                unsafe_allow_html=True,
            )
            if q.get("image"):
                show_question_image(q["image"])
            st.radio("Choose one", q["options"], index=None, key=f"ans_{i}",
                     label_visibility="collapsed")

    if st.button("Submit Test ✔", type="primary"):
        unanswered = [i + 1 for i in range(TOTAL) if st.session_state.get(f"ans_{i}") is None]
        if unanswered:
            st.error("Please answer every question. Unanswered: "
                     + ", ".join(map(str, unanswered)))
        else:
            finish_test(auto=False)


def finish_test(auto: bool = False):
    score = 0
    unit_scores = {u: 0 for u in UNITS}
    answers = []
    for i, q in enumerate(QUESTIONS):
        chosen = st.session_state.get(f"ans_{i}")
        if chosen is None:              # only possible when time ran out
            answers.append("-")
            continue
        idx = q["options"].index(chosen)
        answers.append(LETTERS[idx])
        if idx == q["answer"]:
            score += 1
            unit_scores[q["unit"]] += 1

    elapsed = min(time.time() - st.session_state.start, TEST_SECONDS)
    minutes = round(elapsed / 60, 1)
    status = STATUS_TIME_UP if auto else STATUS_SUBMITTED
    try:
        saved = finalize(st.session_state.name, st.session_state.roll,
                         score, minutes, answers, status)
    except SaveError as exc:
        st.error(f"{exc} Your answers are still on this screen.")
        return

    if not saved:
        # This roll number was already finalized in another window.
        st.session_state.clear()
        st.session_state.login_msg = ("This roll number has already taken the test. "
                                      "Each roll number can attempt it only once.")
        st.rerun()

    st.session_state.score = score
    st.session_state.unit_scores = unit_scores
    st.session_state.minutes = minutes
    st.session_state.auto_submitted = auto
    st.session_state.stage = "done"
    st.rerun()


def done_screen():
    score = st.session_state.score
    pct = round(100 * score / TOTAL, 1)
    passed = pct >= PASS_PERCENT
    css = "result-pass" if passed else "result-fail"
    verdict = "PASS 🎉" if passed else "FAIL"

    render_header("Your test has been submitted and saved.")
    if st.session_state.get("auto_submitted"):
        st.warning("Time was up, so your answers were submitted automatically.")
    st.markdown(
        f'<div class="result-card {css}">'
        f'<div>{verdict}</div>'
        f'<div class="big">{score} / {TOTAL}</div>'
        f'<div>{pct}% · Time taken {st.session_state.minutes} min</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    unit_scores = st.session_state.get("unit_scores", {})
    if unit_scores:
        st.markdown("#### 📊 Marks by Course Outcome")
        cols = st.columns(3)
        for n, (u, (code, co, title)) in enumerate(UNITS.items()):
            with cols[n % 3]:
                st.metric(f"{code} · {co}", f"{unit_scores.get(u, 0)} / 5", help=title)
    st.success("Thank you! Your response is recorded. This roll number cannot take the test again.")

    if st.button("Log out"):
        st.session_state.clear()
        st.rerun()


# ---------- Main ----------

st.set_page_config(page_title="AI & ML Assessment", page_icon="🧠", layout="centered")
generate_question_images()
try:
    ensure_results_file()
except SaveError as exc:
    st.error(str(exc))
    st.info("Configure gcp_service_account and spreadsheet_url in Streamlit app secrets, then restart the app.")
    st.stop()

if "stage" not in st.session_state:
    st.session_state.stage = "login"

if st.session_state.stage == "login":
    login_screen()
elif st.session_state.stage == "quiz":
    quiz_screen()
else:
    done_screen()
