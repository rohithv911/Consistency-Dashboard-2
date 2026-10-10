import sqlite3
import calendar
from datetime import date, datetime, timedelta
from pathlib import Path
import html

import streamlit as st

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "habit_tracker.db"

st.set_page_config(
    page_title="Habit Tracker",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# These defaults are used only when the database is first created.
DEFAULT_HABITS = [
    ("Waking Up at 7 AM", "Morning"),
    ("Drinking 3 Litres of Water", "Health"),
    ("8 Hours of Sleep", "Health"),
]
DEFAULT_TASKS = ["Watch BiggBoss"]


# -------------------- Database --------------------
def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT 'General',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS completions (
                habit_id INTEGER NOT NULL,
                day TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (habit_id, day),
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS personal_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                day TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0
            )
        """)
        habit_count = con.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
        if habit_count == 0:
            con.executemany(
                "INSERT INTO habits(name, category) VALUES (?, ?)",
                DEFAULT_HABITS,
            )
        for task in DEFAULT_TASKS:
            exists = con.execute(
                "SELECT 1 FROM personal_tasks WHERE title=? AND day=?",
                (task, date.today().isoformat()),
            ).fetchone()
            if not exists:
                con.execute(
                    "INSERT INTO personal_tasks(title, day, completed) VALUES (?, ?, 0)",
                    (task, date.today().isoformat()),
                )


def get_habits():
    with connect() as con:
        return con.execute(
            "SELECT id, name, category FROM habits WHERE active=1 ORDER BY id"
        ).fetchall()


def add_habit(name, category):
    name = name.strip()
    if not name:
        return False
    try:
        with connect() as con:
            con.execute(
                "INSERT INTO habits(name, category) VALUES (?, ?)",
                (name, category),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def set_completion(habit_id, day_string, completed):
    with connect() as con:
        con.execute("""
            INSERT INTO completions(habit_id, day, completed)
            VALUES (?, ?, ?)
            ON CONFLICT(habit_id, day)
            DO UPDATE SET completed=excluded.completed
        """, (int(habit_id), day_string, int(completed)))


def is_completed(habit_id, day_string):
    with connect() as con:
        row = con.execute(
            "SELECT completed FROM completions WHERE habit_id=? AND day=?",
            (int(habit_id), day_string),
        ).fetchone()
    return bool(row["completed"]) if row else False


def get_tasks(day_string):
    with connect() as con:
        return con.execute(
            "SELECT id, title, completed FROM personal_tasks WHERE day=? ORDER BY id",
            (day_string,),
        ).fetchall()


def add_task(title, day_string):
    if title.strip():
        with connect() as con:
            con.execute(
                "INSERT INTO personal_tasks(title, day, completed) VALUES (?, ?, 0)",
                (title.strip(), day_string),
            )


def set_task_completion(task_id, completed):
    with connect() as con:
        con.execute(
            "UPDATE personal_tasks SET completed=? WHERE id=?",
            (int(completed), int(task_id)),
        )


def range_completion(habits, days):
    """Return completed checks and possible checks for a list of dates."""
    possible = len(habits) * len(days)
    completed = sum(
        is_completed(habit["id"], day.isoformat())
        for habit in habits
        for day in days
    )
    return completed, possible, (completed / possible if possible else 0.0)


def daily_completion(habits, day):
    total = len(habits)
    completed = sum(is_completed(h["id"], day.isoformat()) for h in habits)
    return completed, total, completed / total if total else 0.0


def pct_bar(value):
    value = max(0, min(100, float(value)))
    return (
        '<div class="progress-track">'
        f'<div class="progress-fill" style="width:{value:.1f}%"></div>'
        '</div>'
    )


init_db()
today = date.today()
now = datetime.now()
habits = get_habits()
day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# -------------------- Styling --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Sacramento&family=Playfair+Display:wght@500;600;700&display=swap');
:root { --pink:#d66fb7; --pink-dark:#b94b94; --pink-soft:#f9eaf3; --pink-pale:#fff8fc; --ink:#35332f; --muted:#88817f; }
.stApp { background:#fff; color:var(--ink); font-family:'DM Sans',sans-serif; }
header[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1500px; padding:.7rem 2.2rem 2.5rem; }
#MainMenu, footer { visibility:hidden; }
.hero-banner {
 position:relative; height:178px; margin:-.1rem -2.2rem .7rem; overflow:hidden;
 display:flex; align-items:center; justify-content:center; text-align:center;
 background:radial-gradient(ellipse at 10% 15%,rgba(255,255,255,.30),transparent 22%),
 radial-gradient(ellipse at 88% 70%,rgba(255,255,255,.22),transparent 25%),
 linear-gradient(115deg,#e9b5d1 0%,#dca3c4 48%,#e7b4d0 100%);
 border-bottom:1px solid #f1dce8;
}
.hero-banner:before,.hero-banner:after { content:"✿  ❀  ❋  ❀  ✿"; position:absolute; color:rgba(255,255,255,.94); font-size:2.3rem; letter-spacing:.18rem; line-height:1.7; width:29%; top:12px; }
.hero-banner:before { left:-1.2rem; transform:rotate(-17deg); }
.hero-banner:after { right:-1.1rem; transform:rotate(16deg); }
.vine { position:absolute; top:0; bottom:0; width:23%; opacity:.75; color:#6f987a; font-size:1.1rem; line-height:1.6; letter-spacing:.35rem; overflow:hidden; }
.vine.left { left:0; transform:rotate(-14deg); } .vine.right { right:0; transform:rotate(14deg); }
.banner-title { color:white; font-family:'Sacramento',cursive; font-size:clamp(3.4rem,6vw,5.3rem); line-height:1; text-shadow:0 1px 1px rgba(255,255,255,.15); z-index:1; }
.sticker { display:inline-block; position:relative; margin-top:-35px; margin-left:1rem; margin-bottom:7px; padding:10px 13px 9px; transform:rotate(-7deg); background:#e86eb5; color:white; border:2px solid #f6c7e3; border-radius:4px 7px 5px 7px; font-size:.62rem; letter-spacing:.08em; line-height:1.25; box-shadow:0 3px 0 #d5a1c0; width:82px; text-align:center; }
.page-title { font-family:'Playfair Display',Georgia,serif; font-size:1.55rem; font-weight:700; margin:0 0 9px; color:#393832; }
.reminder { display:block; background:#fbf0f6; border:1px solid #f7e8f0; color:#51484e; border-radius:3px; padding:11px 15px; margin:6px 0 18px; font-family:'Playfair Display',Georgia,serif; font-size:.83rem; font-style:italic; }
.clock-wrap { display:flex; gap:5px; margin:0 0 13px; }
.clock-card { flex:1; min-width:0; min-height:142px; background:#d66fb7; color:#fff; border-radius:15px; padding:12px 10px 9px; position:relative; overflow:hidden; display:flex; flex-direction:column; justify-content:center; }
.clock-card:after { content:""; position:absolute; left:0; right:0; top:50%; border-top:1px solid rgba(255,255,255,.35); }
.clock-number { font-size:clamp(3rem,5vw,4.6rem); font-weight:700; line-height:.98; text-align:center; letter-spacing:-.07em; }
.clock-foot { display:flex; justify-content:space-between; align-items:end; margin-top:13px; font-size:.63rem; font-weight:700; text-transform:uppercase; }
.side-heading { background:#fbf0f6; color:#4a4148; font-weight:700; font-size:.91rem; padding:5px 8px; margin:10px 0 8px; }
.panel-title { font-family:'Playfair Display',Georgia,serif; font-size:1.25rem; font-weight:700; margin:0 0 3px; }
.panel-subtitle { font-size:.76rem; color:var(--muted); margin-bottom:10px; }
.table-head { color:#7c777b; font-size:.7rem; font-weight:600; padding:8px 2px; border-bottom:1px solid #eee8ed; }
.habit-name { font-family:'Playfair Display',Georgia,serif; font-size:.76rem; color:#514c4e; padding:7px 2px; border-bottom:1px solid #f5f0f3; overflow-wrap:anywhere; }
.progress-track { height:6px; background:#f0edf0; border-radius:10px; overflow:hidden; margin-top:9px; }
.progress-fill { height:100%; background:#d66fb7; border-radius:10px; }
.status-pill { display:inline-block; font-size:.65rem; border-radius:14px; padding:4px 8px; background:#f9eaf3; color:#a44985; white-space:nowrap; }
.status-pill.done { background:#e8f4ec; color:#47815b; }
.metric-card { border:1px solid #f0dce8; background:#fffafd; border-radius:12px; padding:14px 16px; min-height:104px; }
.metric-label { font-size:.76rem; color:#8d7e88; margin-bottom:7px; }
.metric-value { font-family:'Playfair Display',Georgia,serif; color:#a74988; font-size:1.8rem; font-weight:700; line-height:1.15; }
.metric-caption { color:#8d7e88; font-size:.72rem; margin-top:5px; }
.day-cell { border:1px solid #f0e4eb; border-radius:8px; padding:7px 2px; text-align:center; font-size:.7rem; color:#786b74; }
.day-cell.good { background:#f7dceb; border-color:#e6b5d1; color:#8f3e76; }
.day-cell.today { outline:2px solid #d66fb7; outline-offset:1px; }
.calendar-cell { border:1px solid #f0e4eb; border-radius:7px; min-height:60px; padding:5px; background:#fff; }
.calendar-cell .num { font-size:.72rem; color:#7b7077; }
.calendar-cell .mark { font-size:.68rem; margin-top:5px; color:#a44988; font-weight:700; }
.calendar-cell.good { background:#f8e2ef; border-color:#e8bdd6; }
.calendar-cell.perfect { background:#d66fb7; border-color:#d66fb7; }
.calendar-cell.perfect .num,.calendar-cell.perfect .mark { color:white; }
div[data-testid="stCheckbox"] { margin:0; }
.stButton button { border-radius:6px; border:1px solid #e7b5d2; background:#fff7fb; color:#a74988; font-weight:600; }
.stButton button:hover { background:#f9e5f1; border-color:#d66fb7; color:#943b77; }
div[data-testid="stTextInput"] input { border-color:#eed9e5; border-radius:6px; }
div[data-testid="stProgress"] > div > div { background-color:#d66fb7; }
div[data-testid="stProgress"] > div { background:#f2edf1; }
hr { border-color:#f1e8ee; }
@media (max-width:800px) {
 .block-container { padding:.5rem .75rem 2rem; }
 .hero-banner { margin-left:-.75rem; margin-right:-.75rem; height:145px; }
 .clock-card { min-height:105px; padding:8px 5px; }
 .clock-number { font-size:2.7rem; }
 .hero-banner:before,.hero-banner:after { font-size:1.5rem; width:20%; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-banner">
  <div class="vine left">❧<br>✧　❀<br>　❧　✿<br>✧　❀<br>　❧</div>
  <div class="banner-title">Habit Tracker</div>
  <div class="vine right">❀　✧<br>　❧<br>✿　❀<br>　✧　❧<br>❀</div>
</div>
<div class="sticker">BE GENTLE<br>WITH<br>YOURSELF ♡</div>
<div class="page-title">Habit Tracker</div>
<div class="reminder">☁️ &nbsp; Daily Reminder: Drink water!</div>
""", unsafe_allow_html=True)

habits = get_habits()
left, right = st.columns([0.27, 0.73], gap="large")

# Sidebar-style task list and clock
with left:
    hour = now.strftime("%I").lstrip("0") or "12"
    minute = now.strftime("%M")
    ampm = now.strftime("%p")
    weekday = now.strftime("%A").upper()
    st.markdown(f"""
    <div class="clock-wrap">
      <div class="clock-card"><div class="clock-number">{hour}</div><div class="clock-foot"><span>{ampm}</span><span>TIME</span></div></div>
      <div class="clock-card"><div class="clock-number">{minute}</div><div class="clock-foot"><span>♡</span><span>{weekday}</span></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="side-heading">Task List</div>', unsafe_allow_html=True)
    for task in get_tasks(today.isoformat()):
        checked = st.checkbox(task["title"], value=bool(task["completed"]), key=f"task_{task['id']}")
        if checked != bool(task["completed"]):
            set_task_completion(task["id"], checked)
            st.rerun()
    with st.expander("＋ Add a task"):
        with st.form("add_task_form", clear_on_submit=True):
            new_task = st.text_input("Task", placeholder="e.g. Plan tomorrow")
            if st.form_submit_button("Add task", use_container_width=True):
                if new_task.strip():
                    add_task(new_task, today.isoformat())
                    st.rerun()
                else:
                    st.warning("Enter a task name first.")
    done_today, total_today, daily_rate = daily_completion(habits, today)
    st.markdown('<div class="side-heading">Today at a glance</div>', unsafe_allow_html=True)
    st.progress(daily_rate)
    st.caption(f"{done_today} of {total_today} habits completed · {daily_rate:.0%}")

# Main views
with right:
    view_daily, view_weekly, view_monthly = st.tabs(
        ["▦  Daily Tracker", "♡  Weekly Progress", "🌸  Monthly Progress"]
    )

    # Daily tracker
    with view_daily:
        st.markdown('<div class="panel-title">Habit Tracker</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel-subtitle">Weekly checklist · {today.strftime("%A, %d %B %Y")}</div>', unsafe_allow_html=True)
        week_start = today - timedelta(days=today.weekday())
        week_dates = [week_start + timedelta(days=i) for i in range(7)]
        header_cols = st.columns([2.3, *([0.58] * 7), 0.95], gap="small")
        with header_cols[0]:
            st.markdown('<div class="table-head">Task</div>', unsafe_allow_html=True)
        for i, label in enumerate(day_labels):
            with header_cols[i + 1]:
                st.markdown(f'<div class="table-head">{label}</div>', unsafe_allow_html=True)
        with header_cols[8]:
            st.markdown('<div class="table-head">Progress</div>', unsafe_allow_html=True)

        for habit in habits:
            row_cols = st.columns([2.3, *([0.58] * 7), 0.95], gap="small")
            with row_cols[0]:
                st.markdown(f'<div class="habit-name">{html.escape(habit["name"])}</div>', unsafe_allow_html=True)
            week_checks = []
            for i, day in enumerate(week_dates):
                day_string = day.isoformat()
                with row_cols[i + 1]:
                    previous = is_completed(habit["id"], day_string)
                    checked = st.checkbox(
                        f'{habit["name"]} {day_labels[i]}',
                        value=previous,
                        key=f"daily_{habit['id']}_{day_string}",
                        label_visibility="collapsed",
                    )
                    week_checks.append(checked)
                    if checked != previous:
                        set_completion(habit["id"], day_string, checked)
                        st.rerun()
            with row_cols[8]:
                rate = sum(week_checks) / 7
                st.markdown(pct_bar(rate * 100) + f'<div style="font-size:.65rem;color:#8b8288;margin-top:4px">{rate:.0%}</div>', unsafe_allow_html=True)

        with st.expander("＋ Add a habit"):
            with st.form("add_habit_form", clear_on_submit=True):
                habit_name = st.text_input("Habit name", placeholder="e.g. Practice DSA")
                category = st.selectbox("Category", ["Morning", "Health", "Movement", "Mind", "Learning", "General"])
                if st.form_submit_button("Add habit", use_container_width=True):
                    if add_habit(habit_name, category):
                        st.success("Habit added.")
                        st.rerun()
                    else:
                        st.error("Enter a new habit name. Habit names must be unique.")

    # Weekly progress view
    with view_weekly:
        week_start = today - timedelta(days=today.weekday())
        week_dates = [week_start + timedelta(days=i) for i in range(7)]
        elapsed_week_dates = [d for d in week_dates if d <= today]
        weekly_done, weekly_possible, weekly_rate = range_completion(habits, elapsed_week_dates)
        completed_days = sum(
            daily_completion(habits, d)[2] == 1.0 and bool(habits)
            for d in elapsed_week_dates
        )
        best_day = "—"
        if habits and elapsed_week_dates:
            best = max(elapsed_week_dates, key=lambda d: daily_completion(habits, d)[2])
            best_day = best.strftime("%a")
        st.markdown('<div class="panel-title">Your Weekly Progress</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel-subtitle">{week_start.strftime("%d %b")} – {(week_start + timedelta(days=6)).strftime("%d %b %Y")} · future days are not counted as missed</div>', unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Weekly completion</div><div class="metric-value">{weekly_rate:.0%}</div><div class="metric-caption">{weekly_done} of {weekly_possible} possible habit checks</div></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Perfect days</div><div class="metric-value">{completed_days}</div><div class="metric-caption">All habits completed</div></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Best day so far</div><div class="metric-value">{best_day}</div><div class="metric-caption">Highest daily completion rate</div></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown("#### Daily consistency")
        day_cols = st.columns(7, gap="small")
        for i, day in enumerate(week_dates):
            with day_cols[i]:
                if day <= today:
                    d_done, d_total, d_rate = daily_completion(habits, day)
                    css = "good" if d_rate >= .8 else ""
                    today_css = " today" if day == today else ""
                    st.markdown(f'<div class="day-cell {css}{today_css}"><strong>{day_labels[i]}</strong><br>{day.day}<br><span>{d_rate:.0%}</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="day-cell"><strong>{day_labels[i]}</strong><br>{day.day}<br><span>—</span></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown("#### Habit-by-habit consistency")
        for habit in habits:
            done = sum(is_completed(habit["id"], d.isoformat()) for d in elapsed_week_dates)
            rate = done / len(elapsed_week_dates) if elapsed_week_dates else 0
            c1, c2 = st.columns([2.2, 3.8])
            with c1:
                st.markdown(f'<div class="habit-name">{html.escape(habit["name"])}</div>', unsafe_allow_html=True)
            with c2:
                st.markdown(pct_bar(rate * 100) + f'<div style="font-size:.7rem;color:#8b8288;margin-top:4px">{done}/{len(elapsed_week_dates)} days · {rate:.0%}</div>', unsafe_allow_html=True)

    # Monthly progress view
    with view_monthly:
        month_value = st.date_input("Choose month", value=today.replace(day=1), format="YYYY/MM/DD", key="monthly_picker")
        year, month = month_value.year, month_value.month
        month_days_count = calendar.monthrange(year, month)[1]
        month_dates = [date(year, month, day) for day in range(1, month_days_count + 1)]
        elapsed_month_dates = [d for d in month_dates if d <= today] if (year, month) == (today.year, today.month) else (
            month_dates if (year, month) < (today.year, today.month) else []
        )
        month_done, month_possible, month_rate = range_completion(habits, elapsed_month_dates)
        days_with_activity = sum(
            daily_completion(habits, d)[0] > 0 for d in elapsed_month_dates
        )
        perfect_days = sum(
            bool(habits) and daily_completion(habits, d)[2] == 1.0
            for d in elapsed_month_dates
        )
        st.markdown(f'<div class="panel-title">{calendar.month_name[month]} {year} · Monthly Progress</div>', unsafe_allow_html=True)
        if (year, month) > (today.year, today.month):
            st.info("This month is in the future. Progress will appear as you record completed habits.")
        else:
            st.markdown('<div class="panel-subtitle">Monthly totals use elapsed days only for the current month. Past months show the full month.</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Monthly completion</div><div class="metric-value">{month_rate:.0%}</div><div class="metric-caption">{month_done} of {month_possible} habit checks</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Perfect days</div><div class="metric-value">{perfect_days}</div><div class="metric-caption">Every habit completed that day</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Days with progress</div><div class="metric-value">{days_with_activity}</div><div class="metric-caption">At least one habit completed</div></div>', unsafe_allow_html=True)

        st.write("")
        st.markdown("#### Monthly consistency calendar")
        # Calendar grid
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(year, month)
        header = st.columns(7, gap="small")
        for i, label in enumerate(day_labels):
            with header[i]:
                st.markdown(f'<div class="table-head" style="text-align:center">{label}</div>', unsafe_allow_html=True)
        for week in weeks:
            cells = st.columns(7, gap="small")
            for i, day_num in enumerate(week):
                with cells[i]:
                    if day_num == 0:
                        st.markdown('<div style="min-height:60px"></div>', unsafe_allow_html=True)
                    else:
                        d = date(year, month, day_num)
                        done, total, rate = daily_completion(habits, d)
                        css = "perfect" if total > 0 and rate == 1.0 and d <= today else ("good" if done > 0 and d <= today else "")
                        today_mark = " · today" if d == today else ""
                        rate_text = f"{rate:.0%}" if d <= today and (year, month) <= (today.year, today.month) else "—"
                        st.markdown(f'<div class="calendar-cell {css}"><div class="num">{day_num}{today_mark}</div><div class="mark">{rate_text}</div></div>', unsafe_allow_html=True)

        st.write("")
        st.markdown("#### Monthly progress by habit")
        for habit in habits:
            done = sum(is_completed(habit["id"], d.isoformat()) for d in elapsed_month_dates)
            rate = done / len(elapsed_month_dates) if elapsed_month_dates else 0
            c1, c2 = st.columns([2.2, 3.8])
            with c1:
                st.markdown(f'<div class="habit-name">{html.escape(habit["name"])}</div>', unsafe_allow_html=True)
            with c2:
                st.markdown(pct_bar(rate * 100) + f'<div style="font-size:.7rem;color:#8b8288;margin-top:4px">{done}/{len(elapsed_month_dates)} days · {rate:.0%}</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#a99ba4;font-family:\'Playfair Display\',Georgia,serif;font-style:italic;padding:8px;">Be gentle with yourself. Small steps count. ♡</div>', unsafe_allow_html=True)
