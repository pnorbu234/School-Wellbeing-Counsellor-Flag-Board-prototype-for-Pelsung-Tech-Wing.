import json
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SA Wellbeing Flag Board", page_icon="🧭", layout="wide")
DATA_PATH = Path(__file__).parent / "SA_sample_dataset_SYNTHETIC.csv"
STATUS_PATH = Path(__file__).parent / "follow_up_status.json"
FLAGS = ["Urgent", "High", "Review", "None"]
STATUS_OPTIONS = ["Not started", "In progress", "Closed"]

st.markdown("""
<style>
.flag-urgent {background:#7f1d1d;color:white;padding:5px 10px;border-radius:7px;font-weight:800;}
.flag-high {background:#ffedd5;color:#9a3412;padding:5px 10px;border-radius:7px;font-weight:700;}
.flag-review {background:#dbeafe;color:#1e40af;padding:5px 10px;border-radius:7px;font-weight:700;}
.flag-none {background:#e5e7eb;color:#374151;padding:5px 10px;border-radius:7px;font-weight:600;}
.small-note {color:#64748b;font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

def clean_text(value):
    return "" if pd.isna(value) else str(value).strip()

def classify(row):
    if clean_text(row["q6_thoughts_of_self_harm"]).lower() == "yes":
        return "Urgent", "Q6: Student indicated thoughts of self-harm"
    if clean_text(row["q3_bullied"]).lower() == "often" or row["q2_safe_at_home"] == 1:
        reasons = []
        if clean_text(row["q3_bullied"]).lower() == "often":
            reasons.append("Q3: Often bullied")
        if row["q2_safe_at_home"] == 1:
            reasons.append("Q2: Safety at home rated 1")
        return "High", " or ".join(reasons)
    checks = []
    if pd.notna(row["q1_sleep_well"]) and row["q1_sleep_well"] <= 2:
        checks.append("Q1: Poor sleep")
    if clean_text(row["q5_sad_most_days"]).lower() == "yes":
        checks.append("Q5: Sad most days")
    if clean_text(row["q4_trusted_adult"]).lower() == "no":
        checks.append("Q4: No trusted adult")
    if len(checks) >= 2:
        return "Review", "; ".join(checks)
    if clean_text(row["q7_wants_counsellor"]).lower() == "yes":
        return "Review", "Q7: Requested to speak with a counsellor"
    return "None", "No baseline flagging condition met"

def load_status():
    if STATUS_PATH.exists():
        try:
            return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def save_status(status):
    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")

def prepare_data(file):
    df = pd.read_csv(file)
    required = ["student_id", "school", "class", "q1_sleep_well", "q2_safe_at_home",
                "q3_bullied", "q4_trusted_adult", "q5_sad_most_days",
                "q6_thoughts_of_self_harm", "q7_wants_counsellor"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing))
    df["q1_sleep_well"] = pd.to_numeric(df["q1_sleep_well"], errors="coerce")
    df["q2_safe_at_home"] = pd.to_numeric(df["q2_safe_at_home"], errors="coerce")
    results = df.apply(classify, axis=1)
    df["flag"] = [x[0] for x in results]
    df["reason"] = [x[1] for x in results]
    df["data_quality"] = df["q1_sleep_well"].isna().map(
        lambda missing: "Missing sleep response" if missing else "")
    return df

st.title("SA Wellbeing Flag Board")
st.caption("A prototype to help school counsellors prioritise follow-up and help supervisors view privacy-protected patterns.")

with st.sidebar:
    st.header("Navigation")
    page = st.radio("Choose a view", ["Counsellor board", "Supervisor view", "About & rules"])
    st.divider()
    st.caption("Demo dataset only. Do not upload real student wellbeing or mental-health data.")
    uploaded = st.file_uploader("Use a CSV dataset", type=["csv"])

source = uploaded if uploaded is not None else DATA_PATH
try:
    df = prepare_data(source)
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

statuses = load_status()
for sid in df["student_id"].astype(str):
    statuses.setdefault(sid, "Not started")

if page == "Counsellor board":
    st.subheader("Counsellor workspace")
    st.warning("Urgent flags require prompt review by an authorised school counsellor under school safeguarding procedures. This tool does not diagnose or replace professional judgement.")
    counts = df["flag"].value_counts()
    cols = st.columns(4)
    for col, flag in zip(cols, FLAGS):
        col.metric(flag, int(counts.get(flag, 0)))

    c1, c2, c3 = st.columns(3)
    chosen_school = c1.selectbox("School", ["All"] + sorted(df["school"].dropna().unique().tolist()))
    chosen_class = c2.selectbox("Class", ["All"] + sorted(df["class"].dropna().unique().tolist()))
    chosen_flag = c3.selectbox("Flag level", ["All"] + FLAGS)
    search = st.text_input("Search by student ID", placeholder="e.g. S-001")

    view = df.copy()
    if chosen_school != "All":
        view = view[view["school"] == chosen_school]
    if chosen_class != "All":
        view = view[view["class"] == chosen_class]
    if chosen_flag != "All":
        view = view[view["flag"] == chosen_flag]
    if search.strip():
        view = view[view["student_id"].astype(str).str.contains(search.strip(), case=False)]

    priority = {"Urgent": 0, "High": 1, "Review": 2, "None": 3}
    view["_priority"] = view["flag"].map(priority)
    view = view.sort_values(["_priority", "school", "class", "student_id"])
    st.caption(f"Showing {len(view)} of {len(df)} students. Urgent students are prioritised at the top.")

    for _, row in view.iterrows():
        sid, flag = str(row["student_id"]), row["flag"]
        css = {"Urgent": "flag-urgent", "High": "flag-high", "Review": "flag-review", "None": "flag-none"}[flag]
        with st.container(border=True):
            left, middle, right = st.columns([2, 4, 3])
            left.markdown(f"**{sid}**")
            left.caption(f'{row["school"]} · Class {row["class"]}')
            left.markdown(f'<span class="{css}">{flag}</span>', unsafe_allow_html=True)
            middle.write(f'**Reason:** {row["reason"]}')
            if row["data_quality"]:
                middle.info("Data quality: " + row["data_quality"])
            new_status = right.selectbox("Follow-up status", STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(statuses.get(sid, "Not started")), key=f"status_{sid}")
            if new_status != statuses.get(sid):
                statuses[sid] = new_status
                save_status(statuses)
                st.toast(f"Saved follow-up status for {sid}")
            if flag != "None":
                right.caption("Update after counsellor review.")

    if view.empty:
        st.info("No students match these filters.")

elif page == "Supervisor view":
    st.subheader("Supervisor overview")
    st.info("Aggregated counts only. Student IDs and free-text comments are not shown here.")
    st.metric("Students in dataset", len(df))
    summary = (df.groupby(["school", "class", "flag"]).size().unstack(fill_value=0)
                 .reindex(columns=FLAGS, fill_value=0).reset_index())
    group_sizes = df.groupby(["school", "class"]).size().to_dict()

    def safe_count(value, group_total):
        if group_total < 5 or int(value) < 5:
            return "<5"
        return str(int(value))

    rows = []
    for _, row in summary.iterrows():
        total = int(group_sizes[(row["school"], row["class"])])
        rows.append({"School": row["school"], "Class": row["class"],
                     "Students": "<5" if total < 5 else str(total),
                     **{flag: safe_count(row[flag], total) for flag in FLAGS}})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("Groups smaller than five and individual flag counts below five are suppressed as <5.")
    school_summary = (df.groupby(["school", "flag"]).size().unstack(fill_value=0)
                        .reindex(columns=FLAGS, fill_value=0))
    st.markdown("#### Flag distribution by school")
    st.bar_chart(school_summary)

elif page == "About & rules":
    st.subheader("How the prototype works")
    st.markdown("""
**Baseline rules (first match wins):**
1. **Urgent:** Q6 = Yes.
2. **High:** Q3 = Often, or Q2 = 1.
3. **Review:** any two of Q1 ≤ 2, Q5 = Yes, Q4 = No; or Q7 = Yes.
4. **None:** all other responses.

**Extra improvement — missing-response indicator:** a missing sleep response is visibly identified for the counsellor. It does not automatically increase the flag.

**Follow-up statuses:** Not started, In progress, and Closed. Statuses are stored in a local JSON file and survive a page refresh while the app's file storage remains available.

**Limitations:** this prototype has no authentication, role-based access control, encrypted database, audit log, or production-grade backup. It must not be used with real student data.

An Urgent flag is a prompt for human review, not a diagnosis or a substitute for safeguarding procedures or professional judgement.
""")

st.divider()
st.caption("Pelsung Tech Wing · SA Wellbeing Platform · Streamlit prototype")
