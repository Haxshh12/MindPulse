from __future__ import annotations
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import random
from utils.user_utils import save_user_inputs, save_feedback, init_files
from utils.admin_utils import load_psychologists, load_user_inputs

import streamlit.components.v1 as components
# Risk colors used by the pill
_RISK_COLORS = {
    "Low": "#16a34a",
    "Moderate": "#f59e0b",  
    "High": "#dc2626",
}

def _pill(text: str, bg: str) -> None:
    """Render a soft rounded pill badge."""
    st.markdown(
        f"""
        <div style="display:inline-block;padding:0.25rem 0.6rem;border-radius:9999px;
                    background:{bg};color:white;font-weight:600">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )

def _metric_card(label: str, value: str, help_text: Optional[str] = None) -> None:
    """Small KPI card. Works on Streamlit >=1.31 (border=True)."""
    try:
        with st.container(border=True):
            st.markdown(f"### {label}")
            st.markdown(
                f"<div style='font-size:2rem;font-weight:700'>{value}</div>",
                unsafe_allow_html=True,
            )
            if help_text:
                st.caption(help_text)
    except TypeError:
        
        st.markdown(f"**{label}**")
        st.markdown(f"<div style='font-size:1.6rem;font-weight:700'>{value}</div>", unsafe_allow_html=True)
        if help_text:
            st.caption(help_text)
        st.markdown("---")

def _safe_get(d: Dict[str, Any], key: str, default: Any = None):
    """Safe dict getter that won’t explode if d is None or not a mapping."""
    try:
        return d.get(key, default)
    except Exception:
        return default
    
st.set_page_config(page_title="MindPulse • Dashboard", page_icon="🧠", layout="wide")

_RISK_COLORS = {"Low": "#16a34a", "Moderate": "#f59e0b", "High": "#dc2626"}
_LIFESTYLE_MAPS = {
    "exercise": {"None": 0, "1-2 days/week": 3, "3-5 days/week": 6, "Daily": 9},
    "diet": {"Poor": 2, "Average": 5, "Good": 7, "Excellent": 9},
}

@st.cache_data(show_spinner=False)
def _cached_load_user_inputs() -> Optional[pd.DataFrame]:
    try:
        df = load_user_inputs()
        if df is not None and not df.empty:
            # Normalize
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            cols = [c for c in ["stress_level","anxiety_level","depression_level","sleep_hours"] if c in df.columns]
            for c in cols:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    except Exception:
        return None


def _safe_session_name() -> str:
    return st.session_state.get("name", "User")


# Risk model 
def compute_risk_score(form_data):
    def _num(x, default=0.0):
        try:
            return float(x)
        except Exception:
            return float(default)

    # Base (your original)
    s = _num(form_data.get("stress_level", 0))
    a = _num(form_data.get("anxiety_level", 0))
    d = _num(form_data.get("depression_level", 0))
    score = s * 0.45 + a * 0.35 + d * 0.20
    nudges = 0.0
    sleep = _num(form_data.get("sleep_hours", 0))
    if sleep < 6:
        nudges += 0.4
    elif 7 <= sleep <= 9:
        nudges -= 0.2

    exercise = (form_data.get("exercise_freq") or "").strip()
    if exercise in {"None"}:
        nudges += 0.2
    elif exercise in {"3-5 days/week", "Daily"}:
        nudges -= 0.2

    diet = (form_data.get("diet_quality") or "").strip()
    if diet in {"Poor"}:
        nudges += 0.2
    elif diet in {"Good", "Excellent"}:
        nudges -= 0.1

    wlb = (form_data.get("work_life_balance") or "").strip()
    if wlb in {"Poor"}:
        nudges += 0.3
    elif wlb in {"Good", "Excellent"}:
        nudges -= 0.1

    social = (form_data.get("social_interaction") or "").strip()
    if social in {"Rarely"}:
        nudges += 0.2
    elif social in {"Often", "Daily"}:
        nudges -= 0.1

    if (form_data.get("past_mental_illness") or "") == "Yes":
        nudges += 0.2
    if (form_data.get("current_medication") or "") == "Yes":
        nudges += 0.1

    score = score + max(-1.0, min(1.0, nudges))
    return round(max(0.0, min(10.0, score)), 1)


# ----------------- Form -----------------
def mental_health_form():
    with st.form("mental_health_form", clear_on_submit=False):
        st.header("📝 Mental Health Self-Assessment")
        st.caption("Honest responses help us surface more useful insights. You can skip anything you’re not comfortable sharing.")

        
        st.subheader("Lifestyle")
        c1, c2, c3 = st.columns(3)
        with c1:
            age = st.number_input("Age", min_value=10, max_value=100, step=1, value=25,
                                  help="Used only for aggregate insights.")
        with c2:
            gender = st.selectbox("Gender", ["Male ♂️", "Female ♀️", "Other 🏳️‍🌈", "Prefer not to say ❌"])
        with c3:
            occupation = st.text_input("Occupation (optional)", placeholder="e.g. Student, Engineer")

        c4, c5, c6 = st.columns(3)
        with c4:
            sleep_hours = st.slider("Average sleep hours per night", 0, 12, 7,
                                    help="Most adults benefit from ~7–9 hours.")
        with c5:
            exercise_freq = st.selectbox("Exercise frequency",
                                         ["None", "1-2 days/week", "3-5 days/week", "Daily"])
        with c6:
            diet_quality = st.select_slider("Diet quality", ["Poor🔴", "Average🟠", "Good🟢", "Excellent🔵"])

        
        st.subheader("Emotional & Mental State")
        c7, c8, c9 = st.columns(3)
        with c7:
            stress_level = st.slider("Stress (0 = none, 10 = extreme)", 0, 10, 5,
                                     help="Your overall perceived stress right now.")
        with c8:
            anxiety_level = st.slider("Anxiety (0 = none, 10 = extreme)", 0, 10, 4,
                                      help="Worry, restlessness, tension, racing thoughts.")
        with c9:
            depression_level = st.slider("Low mood (0 = none, 10 = extreme)", 0, 10, 3,
                                         help="Sadness, loss of interest, low energy.")

        c10, c11, c12 = st.columns(3)
        with c10:
            social_interaction = st.selectbox("How often do you socialize?",
                                              ["Rarely", "Sometimes", "Often", "Daily"])
        with c11:
            work_life_balance = st.selectbox("Work-life balance", ["Poor 🔴", "Fair 🟠", "Good 🟢", "Excellent 🔵"])
        with c12:
            coping_methods = st.multiselect(
                "Coping methods you use",
                ["Meditation 🧘‍♂️", "Exercise 🏋️‍♂️","Dancing 💃", "Hobbies 🎭","Running 🏃‍♂️", "Talking to friends/family 🫂", "Therapy 🪷","Sketching ✒️","Journaling 📚", "Other 🎪"],
                help="Select all that apply."
            )

        
        with st.expander("➕ Optional quick screens"):
            phq2 = st.slider("PHQ-2: Down, depressed, or hopeless (0–5)", 0, 5, 0,
                             help="0=None, 1=Several days, 2=More than half, 3=Nearly every day")
            gad2 = st.slider("GAD-2: Feeling nervous, anxious, or on edge (0–5)", 0, 5, 0,
                             help="0=None, 1=Several days, 2=More than half, 3=Nearly every day")

        
        st.subheader("Medical & Psychological History")
        c13, c14 = st.columns(2)
        with c13:
            past_mental_illness = st.radio("Past mental health diagnosis?", ["No", "Yes"], horizontal=True)
        with c14:
            current_medication = st.radio("Currently on medication for mental health?", ["No", "Yes"], horizontal=True)
        medication_details = ""
        if current_medication == "Yes":
            medication_details = st.text_area("If yes, specify medication (optional)")

        
        with st.expander("🛡️ Protective factors (optional)"):
            support_level = st.select_slider("Perceived social support", ["Least 😣","Low 🙁", "Medium 😐", "High 🙂","Very High 😊"], value="Medium 😐")
            purpose_level = st.select_slider("Sense of p urpose/meaning", ["Low", "Medium", "High"], value="Medium")

        
        st.subheader("💬 Quick note (optional)")
        feedback_short = st.text_area("How are you feeling right now? Any quick notes or suggestions?")

        submitted = st.form_submit_button("Submit Assessment ✨")

    if submitted:
        return {
            # original fields (unchanged keys)
            "age": age,
            "gender": gender,
            "occupation": occupation,
            "sleep_hours": sleep_hours,
            "exercise_freq": exercise_freq,
            "diet_quality": diet_quality,
            "stress_level": stress_level,
            "anxiety_level": anxiety_level,
            "depression_level": depression_level,
            "social_interaction": social_interaction,
            "work_life_balance": work_life_balance,
            "coping_methods": coping_methods,
            "past_mental_illness": past_mental_illness,
            "current_medication": current_medication,
            "medication_details": medication_details,
            "feedback": feedback_short,
            # new optional fields (safe to ignore elsewhere)
            "phq2": phq2,
            "gad2": gad2,
            "support_level": support_level,
            "purpose_level": purpose_level,
        }
    return None


# ----------------- Visualizations -----------------
def radar_chart(form_data):
    categories = ["Stress", "Anxiety", "Depression"]
    values = [
        float(form_data.get("stress_level", 0)),
        float(form_data.get("anxiety_level", 0)),
        float(form_data.get("depression_level", 0)),
    ]
    fig = go.Figure(go.Scatterpolar(
        r=values, theta=categories, fill="toself", name="Emotional",
        hovertemplate="%{theta}: %{r}/10<extra></extra>"
    ))
    fig.update_layout(
        title="Emotional Radar",
        polar=dict(radialaxis=dict(range=[0, 10], tickmode="linear", tick0=0, dtick=2)),
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def lifestyle_bar_chart(form_data):
    exercise_map = {"None": 0, "1-2 days/week": 3, "3-5 days/week": 6, "Daily": 9}
    diet_map = {"Poor": 2, "Average": 5, "Good": 7, "Excellent": 9}
    data = {
        "Factor": ["Sleep Hours", "Exercise (scaled)", "Diet (scaled)"],
        "Score": [
            float(form_data.get("sleep_hours", 0)),
            exercise_map.get(form_data.get("exercise_freq", ""), 0),
            diet_map.get(form_data.get("diet_quality", ""), 5),
        ],
    }
    df = pd.DataFrame(data)
    fig = px.bar(
        df, x="Factor", y="Score", text="Score", title="Lifestyle Summary",
    )
    fig.update_traces(textposition="outside", hovertemplate="%{x}: %{y}<extra></extra>")
    fig.update_yaxes(range=[0, 12], dtick=2)
    # Visual sleep target band (7–9h)
    fig.add_shape(type="rect", xref="paper", x0=0, x1=1, y0=7, y1=9,
                  line=dict(width=0), fillcolor="rgba(86,180,233,0.12)", layer="below")
    fig.add_annotation(x=0.02, y=9.05, xref="paper", yref="y",
                       text="Recommended sleep range", showarrow=False, font=dict(size=10, color="#4b5563"))
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def emotional_pie(form_data):
    labels = ["Stress", "Anxiety", "Depression"]
    vals = [
        float(form_data.get("stress_level", 0)),
        float(form_data.get("anxiety_level", 0)),
        float(form_data.get("depression_level", 0)),
    ]
    fig = px.pie(values=vals, names=labels, title="Emotional Distribution", hole=0.35)
    fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}: %{value}/10<extra></extra>")
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def risk_gauge(score):
    score = float(score or 0)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Overall Risk Score (0–10)"},
        gauge={
            "axis": {"range": [0, 10]},
            "bar": {"thickness": 0.25},
            "steps": [
                {"range": [0, 4], "color": "#86efac"},
                {"range": [4, 7], "color": "#fde68a"},
                {"range": [7, 10], "color": "#fca5a5"},
            ],
        },
        number={"suffix": " / 10"},
    ))
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def trend_line_for_user(email):
    """If user has historical data, plot trend of stress/anxiety/depression over time."""
    try:
        df_all = load_user_inputs()
        if df_all is None or df_all.empty:
            return None
        # ensure timestamp parsed safely
        df_all["timestamp"] = pd.to_datetime(df_all["timestamp"], errors="coerce")
        df_user = (
            df_all[df_all["email"].astype(str).str.lower() == str(email).lower()]
            .dropna(subset=["timestamp"])
            .sort_values("timestamp")
        )
        if df_user.shape[0] < 2:
            return None  # not enough points to show trend
        plot_df = df_user[["timestamp", "stress_level", "anxiety_level", "depression_level"]].melt(
            id_vars="timestamp", var_name="Metric", value_name="Value"
        )
        fig = px.line(plot_df, x="timestamp", y="Value", color="Metric", markers=True,
                      title="Your mental health trend over time")
        fig.update_yaxes(range=[0, 10], dtick=2)
        fig.update_traces(hovertemplate="%{x|%Y-%m-%d %H:%M}<br>%{fullData.name}: %{y}<extra></extra>")
        fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
        return fig
    except Exception:
        return None



def correlation_heatmap():
    """Show correlation heatmap if dataset has enough numeric data."""
    try:
        df_all = load_user_inputs()
        if df_all is None or df_all.empty or df_all.shape[0] < 5:
            return None
        # select numeric columns of interest
        cols = ["stress_level", "anxiety_level", "depression_level", "sleep_hours"]
        numeric = df_all[cols].apply(pd.to_numeric, errors="coerce").dropna()
        if numeric.shape[0] < 5:
            return None
        corr = numeric.corr()
        fig = px.imshow(corr, text_auto=True, title="Correlation heatmap (population)",
                        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                        labels=dict(color="r"))
        fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
        return fig
    except Exception:
        return None

# ===================== Main Dashboard ===================== #

def user_dashboard() -> None:
    """
    Upgraded user dashboard:
    - Persistent session_state for form + computed KPI (prevents snapbacks on downloads)
    - Clear risk explanations and a Safety Check for high risk
    - Stable, accessible section navigation (radio) to avoid tab snapback
    - Graceful fallbacks if helper functions or data are missing
    - Stable download buttons with keys
    """
    if not st.session_state.get("logged_in", False):
        st.warning("⚠️ Please login first.")
        st.stop()

    
    try:
        init_files()  
    except Exception:

        pass

    # 3) Greeting hero
    try:
        username = _safe_session_name()  # type: ignore[name-defined]
    except Exception:
        username = "there"

    st.markdown(
        f"""
        <div style="background:linear-gradient(45deg,#07293d,#c098cf);padding:14px;border-radius:12px;color:white;">
          <div style="font-size:1.2rem;font-weight:700">👋 Welcome, {username}</div>
          <div style="color:#c7d2fe;font-size:0.92rem">Complete the assessment below to receive insights, suggestions, and a downloadable report.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4) Collect form data with safe loading
    # prefer persisted submission to keep UI stable across re-runs (downloads)
    persisted = st.session_state.get("mp_form")
    form_data: Optional[Dict[str, Any]] = None
    form_error = None
    try:
        form_data = mental_health_form()  # type: ignore[name-defined]
    except Exception as e:
        # keep the error for later display, do not crash
        form_error = e

    if form_error:
        st.error("The assessment form couldn't be loaded — please contact the admin.")
        st.exception(form_error)
        st.stop()

    # when user submits, store to session (prevents download/button rerun losing state)
    if form_data:
        st.session_state["mp_form"] = form_data
        st.session_state["mp_email"] = st.session_state.get("email", "")
        st.session_state["mp_name"] = st.session_state.get("name", username)

    # prefer session persisted form_data
    form_data = st.session_state.get("mp_form", form_data)
    email = st.session_state.get("mp_email", st.session_state.get("email", ""))
    name = st.session_state.get("mp_name", username)

    # if not submitted yet, don't render post-submit UI
    if not form_data:
        return

    # 5) Consent & save (show once; user may opt out)
    st.divider()
    with st.container(border=True):
        st.subheader("🔒 Consent & data use")
        st.write(
            "Your answers can be saved to generate trends for you. "
            "You can export or delete them anytime from Settings."
        )

        # Widget defines and stores the key in session_state automatically.
        consent = st.checkbox(
            "I consent to save this submission for insights and reports.",
            value=st.session_state.get("mp_consent", True),
            key="mp_consent",
        )

        if consent:
            try:
                save_user_inputs(form_data, email=email, name=name)
                st.success("✅ Assessment submitted and saved.")
            except Exception as e:
                st.warning("We couldn't save your submission. Insights will still be shown for this session.")
                st.info("Admins: ensure write permissions and CSV schema alignment.")
                st.exception(e)
        else:
            st.info("Submission not saved. Insights will only persist for this session.")


    # 6) Risk score & label, with safe fallback
    def _risk_label(v: float) -> str:
        return "High" if v >= 7 else "Moderate" if v >= 4 else "Low"

    try:
        risk_score = float(compute_risk_score(form_data))  # type: ignore[name-defined]
    except Exception:
        stress = float(_safe_get(form_data, "stress_level", 0) or 0)
        anxiety = float(_safe_get(form_data, "anxiety_level", 0) or 0)
        depression = float(_safe_get(form_data, "depression_level", 0) or 0)
        risk_score = float(min(10, round((stress + anxiety + depression) / 3, 1)))

    risk_label = _risk_label(risk_score)
    st.session_state["mp_risk_score"] = risk_score
    st.session_state["mp_risk_label"] = risk_label

    # create concise explanation bullets (mirrors compute_risk nudges if present)
    def _risk_explanations(fd: Dict[str, Any]) -> List[str]:
        expl = []
        try:
            sleep = float(_safe_get(fd, "sleep_hours", 0) or 0)
            if sleep < 6:
                expl.append("Short sleep (<6h) — consider a consistent bedtime routine.")
            elif 7 <= sleep <= 9:
                expl.append("Good sleep range — positive for mood regulation.")
            ex = (fd.get("exercise_freq") or "").strip()
            if ex == "None":
                expl.append("Try light activity 2–3 times/week to help reduce stress.")
            diet = (fd.get("diet_quality") or "").strip()
            if diet == "Poor":
                expl.append("Improving diet quality can support energy & mood.")
            social = (fd.get("social_interaction") or "").strip()
            if social == "Rarely":
                expl.append("Small social check-ins can be beneficial.")
        except Exception:
            pass
        return expl[:4]

    # 7) Summary KPIs & narrative
    st.subheader("📊 Summary")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    with c1:
        # prefer the custom metric card if available; else fallback to st.metric
        try:
            _metric_card("Risk Score", f"{risk_score:.1f} / 10", "Composite (0–10)")  # type: ignore[name-defined]
        except Exception:
            st.metric("Risk Score", f"{risk_score:.1f} / 10")
    with c2:
        try:
            _metric_card("Stress", str(_safe_get(form_data, "stress_level", "-")))
        except Exception:
            st.metric("Stress", str(_safe_get(form_data, "stress_level", "-")))
    with c3:
        try:
            _metric_card("Sleep (hrs)", str(_safe_get(form_data, "sleep_hours", "-")))
        except Exception:
            st.metric("Sleep (hrs)", str(_safe_get(form_data, "sleep_hours", "-")))
    with c4:
        st.markdown("**Status**")
        try:
            _pill(f"{risk_label}", _RISK_COLORS[risk_label])  # type: ignore[name-defined]
        except Exception:
            st.markdown(f"**{risk_label}**")
        st.caption("Weighted from stress/anxiety/depression. Lifestyle nudges applied.")

    # quick domain insight
    stress = _safe_get(form_data, "stress_level", 0) or 0
    anxiety = _safe_get(form_data, "anxiety_level", 0) or 0
    depression = _safe_get(form_data, "depression_level", 0) or 0
    top_domain = max([("Stress", stress), ("Anxiety", anxiety), ("Depression", depression)], key=lambda x: x[1])[0]
    st.info(f"Your strongest concern right now appears to be **{top_domain}**.")

    # risk explanation expander (concise)
    with st.expander("Why this score? (personalised tips)", expanded=True):
        tips = _risk_explanations(form_data)
        if tips:
            for t in tips:
                st.markdown(f"• {t}")
        else:
            st.markdown("• No extra lifestyle nudges detected. Keep tracking over time for better insights.")

    # high-risk supportive block
    if risk_label == "High":
        with st.container(border=True):
            st.markdown("### 🛟 Safety & support (non-diagnostic)")
            st.write(
                "If you're feeling overwhelmed or thinking about self-harm, please contact local emergency services or a crisis hotline immediately."
            )
            # option to show local hotline if admin provided (safe attempt)
            try:
                psych_df = load_psychologists()  # type: ignore[name-defined]
                if psych_df is not None and not getattr(psych_df, "empty", True):
                    st.info("You can also contact a listed professional in the Recommendations tab below.")
            except Exception:
                pass

    # 8) Persistent section navigation (radio prevents tab snapback)
    st.divider()
    section = st.radio(
        "Navigate",
        ["Visualizations", "Recommendations", "Report", "Feedback"],
        key="mp_section",
        horizontal=True,
    )

    # 9) Visualizations section
    if section == "Visualizations":
        try:
            col1, col2 = st.columns(2)
            with col1:
                try:
                    st.plotly_chart(radar_chart(form_data), use_container_width=True)  # type: ignore[name-defined]
                except Exception:
                    st.info("Radar unavailable.")
                try:
                    st.plotly_chart(emotional_pie(form_data), use_container_width=True)  # type: ignore[name-defined]
                except Exception:
                    pass
            with col2:
                try:
                    st.plotly_chart(lifestyle_bar_chart(form_data), use_container_width=True)  # type: ignore[name-defined]
                except Exception:
                    pass
                try:
                    st.plotly_chart(risk_gauge(risk_score), use_container_width=True)  # type: ignore[name-defined]
                except Exception:
                    st.progress(min(risk_score, 10) / 10.0, text="Risk gauge")

            # historical trend (if available)
            try:
                trend_fig = trend_line_for_user(email)  # type: ignore[name-defined]
            except Exception:
                trend_fig = None
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True)
            else:
                st.caption("No historical submissions yet — submit over time to see trends.")

            # cohort/population heatmap (if available)
            try:
                heat = correlation_heatmap()  # type: ignore[name-defined]
            except Exception:
                heat = None
            if heat is not None:
                st.plotly_chart(heat, use_container_width=True)
        except Exception as e:
            st.error("We couldn't render one or more charts.")
            st.exception(e)

    # 10) Recommendations section (robust UX)
    if section == "Recommendations":
        st.subheader("🩺 Recommended Psychologists / Counselors")
        suggestions: List[Dict[str, Any]] = st.session_state.get("_mp_suggestions", [])
        load_err = None
        try:
            if not suggestions:
                psych_df = load_psychologists()  # type: ignore[name-defined]
                if psych_df is not None and getattr(psych_df, "empty", True) is False:
                    rng = random.Random(abs(hash(email or name)) % (2**32 - 1))
                    n = min(3, len(psych_df))
                    idxs = rng.sample(range(len(psych_df)), k=n)
                    suggestions = psych_df.iloc[idxs].to_dict(orient="records")
                    st.session_state["_mp_suggestions"] = suggestions
        except Exception as e:
            load_err = e
            suggestions = []

        if suggestions:
            cols = st.columns(len(suggestions))
            for i, p in enumerate(suggestions):
                with cols[i]:
                    st.markdown(f"**{_safe_get(p,'name','N/A')}**")
                    contact = []
                    if _safe_get(p, "specialty"): contact.append(f"_Specialty_: {_safe_get(p,'specialty')}")
                    if _safe_get(p, "email"): contact.append(f"📧 {_safe_get(p,'email')}")
                    if _safe_get(p, "phone"): contact.append(f"📞 {_safe_get(p,'phone')}")
                    st.write("<br>".join(contact), unsafe_allow_html=True)
                    if _safe_get(p, "booking_url"):
                        try:
                            st.link_button("Book appointment", _safe_get(p, "booking_url"))
                        except Exception:
                            st.button("Book (open link)", key=f"book_{i}")
        else:
            st.warning("No psychologists configured for your region yet.")
            if load_err and st.session_state.get("role") == "admin":
                st.caption(f"Admin debug: load_psychologists() error — {type(load_err).__name__}: {load_err}")
            # helpful fallbacks for users
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("📞 Emergency services"):
                    st.info("Please call your local emergency number immediately.")
            with col_b:
                if st.button("📲 Request admin callback"):
                    try:
                        save_feedback(email, name, 5, "User requested provider callback.")  # ensure admins see request
                        st.success("Admin notified — they'll follow up when available.")
                    except Exception:
                        st.info("Request saved locally for session (admin may be offline).")
            with col_c:
                if st.button("🔎 Load demo suggestions"):
                    demo = [
                        {"name": "Dr. Demo A", "email": "demoA@example.com", "phone": "+1-555-0001", "specialty": "CBT"},
                        {"name": "Dr. Demo B", "email": "demoB@example.com", "phone": "+1-555-0002", "specialty": "Stress"},
                        {"name": "Dr. Demo C", "email": "demoC@example.com", "phone": "+1-555-0003", "specialty": "Anxiety"},
                    ]
                    st.session_state["_mp_suggestions"] = demo
                    st.experimental_rerun()

        st.caption("If you're in immediate danger or thinking about self-harm, contact local emergency services or crisis hotlines now.")

    # 11) Report section (stable downloads that won't lose your state)
    if section == "Report":
        st.subheader("📄 Downloadable Report")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        risk_score = st.session_state.get("mp_risk_score", risk_score)
        risk_label = st.session_state.get("mp_risk_label", risk_label)
        suggestions = st.session_state.get("_mp_suggestions", [])

        report_lines = [
            f"MindPulse Report - {timestamp}",
            f"Name: {name}",
            f"Email: {email}",
            f"Risk Score: {risk_score:.1f} / 10 ({risk_label})",
            "",
            "Raw scores:",
            f" - Stress: {_safe_get(form_data,'stress_level','N/A')}",
            f" - Anxiety: {_safe_get(form_data,'anxiety_level','N/A')}",
            f" - Depression: {_safe_get(form_data,'depression_level','N/A')}",
            f" - Sleep hours: {_safe_get(form_data,'sleep_hours','N/A')}",
            f" - Exercise frequency: {_safe_get(form_data,'exercise_freq','N/A')}",
            f" - Diet quality: {_safe_get(form_data,'diet_quality','N/A')}",
            "",
            "Recommended professionals:",
        ]
        try:
            for p in suggestions:
                report_lines.append(f" - {_safe_get(p,'name','')} | {_safe_get(p,'email','')} | {_safe_get(p,'phone','')}")
        except Exception:
            pass

        txt = "\n".join(report_lines)
        md = (
            f"# MindPulse Report\n\n"
            f"**Generated:** {timestamp}\n\n"
            f"**Name:** {name}  \n"
            f"**Email:** {email}  \n"
            f"**Risk:** {risk_score:.1f}/10 — {risk_label}\n\n"
            f"## Raw Scores\n"
            f"- Stress: {_safe_get(form_data,'stress_level','N/A')}\n"
            f"- Anxiety: {_safe_get(form_data,'anxiety_level','N/A')}\n"
            f"- Depression: {_safe_get(form_data,'depression_level','N/A')}\n"
            f"- Sleep hours: {_safe_get(form_data,'sleep_hours','N/A')}\n"
        )
        raw = json.dumps(
            {"generated_at": timestamp, "name": name, "email": email, "risk_score": risk_score, "risk_label": risk_label, "form": form_data, "suggestions": suggestions},
            indent=2,
        )

        # Use stable keys so Streamlit recognizes the widgets across re-runs
        st.download_button("Download text report", txt, file_name=f"mindpulse_report_{datetime.now():%Y%m%d_%H%M%S}.txt", key="dl_txt")
        st.download_button("Download Markdown report", md, file_name=f"mindpulse_report_{datetime.now():%Y%m%d_%H%M%S}.md", key="dl_md")
        st.download_button("Download JSON (raw)", raw, file_name=f"mindpulse_data_{datetime.now():%Y%m%d_%H%M%S}.json", mime="application/json", key="dl_json")

    # 12) Feedback section
    if section == "Feedback":
        st.subheader("💬 Detailed Feedback (optional)")
        with st.form(key="feedback_form", clear_on_submit=True):
            rating = st.slider("Rate your experience (1 = poor,10 = excellent)", 1, 10, 0)
            feedback_long = st.text_area("Share detailed feedback or suggestions (optional)")
            submitted_fb = st.form_submit_button("Submit Feedback")
        if submitted_fb:
            if (feedback_long or "").strip():
                try:
                    save_feedback(email, name, rating, feedback_long.strip())  # type: ignore[name-defined]
                    st.success("✅ Thanks for your feedback — it has been recorded.")
                    try:
                        st.toast("Feedback submitted. Thank you!")
                    except Exception:
                        pass
                except Exception as e:
                    st.error("Couldn't save feedback.")
                    st.exception(e)
            else:
                st.warning("Please enter some feedback text before submitting.")

    # 13) Delightful but subtle effects
    try:
        if risk_label == "Low":
            st.balloons
        elif risk_label == "Moderate":
            st.balloons
        elif risk_label == "High":
            st.snow
    except Exception as e:
        # log or show admin info if you want to debug later
        # st.write(f"Animation error: {e}")
        pass


    # end user_dashboard
