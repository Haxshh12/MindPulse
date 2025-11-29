from __future__ import annotations
import io
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.admin_utils import (
    load_users, save_users,
    load_user_inputs, save_user_inputs,
    load_psychologists, save_psychologists, append_psychologist,
    load_feedback, save_feedback, clear_feedback,
)

# ----------------- Page Setup -----------------
st.set_page_config(page_title="MindPulse • Admin Studio", page_icon="🧰", layout="wide")

# ----------------- Theming (simple CSS polish) -----------------
st.markdown(
    """
    <style>
      .mp-hero{background:linear-gradient(90deg,#111827, #1f2937 60%, #111827); padding:18px 20px; border-radius:14px; color:white;}
      .mp-hero h1{font-size:1.4rem; margin:0;}
      .mp-hero p{margin:4px 0 0 0; color:#d1d5db;}
      .mp-chip{display:inline-block; padding:4px 10px; border-radius:9999px; background:#e5e7eb; margin-right:6px; font-size:12px}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- Caching Helpers -----------------
@st.cache_data(show_spinner=False)
def _safe_load_users() -> pd.DataFrame:
    try:
        df = load_users()
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def _safe_load_inputs() -> pd.DataFrame:
    try:
        df = load_user_inputs()
        if df is None:
            return pd.DataFrame()
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        for col in ["stress_level","anxiety_level","depression_level","sleep_hours"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def _safe_load_psych() -> pd.DataFrame:
    try:
        df = load_psychologists()
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def _safe_load_feedback() -> pd.DataFrame:
    try:
        df = load_feedback()
        if df is None:
            return pd.DataFrame()
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        if "rating" in df.columns:
            df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()

# ----------------- Utilities -----------------

def _csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _excel_pack(sheets: Dict[str, pd.DataFrame]) -> bytes:
    import io
    import pandas as pd

    output = io.BytesIO()

    # 1) Choose a working engine
    engine = None
    try:
        import openpyxl  # noqa: F401
        engine = "openpyxl"
    except Exception:
        try:  
            engine = "xlsxwriter"
        except Exception:
            engine = None

    def _safe_sheet_name(name: str, used: set) -> str:
        base = (name or "Sheet").strip() or "Sheet"
        base = base[:31]
        if base not in used:
            used.add(base)
            return base
        # Deduplicate: Sheet, Sheet (1), Sheet (2)...
        i = 1
        while True:
            candidate = f"{base[:28]} ({i})"[:31]
            if candidate not in used:
                used.add(candidate)
                return candidate
            i += 1

    # 2) Write with the best available engine
    if engine is None:
        # Last-ditch fallback: return a tiny CSV-like bytes to avoid crashing the UI
        # (or raise a friendly error). Recommended: install openpyxl or XlsxWriter.
        return pd.DataFrame({"Info": ["Install openpyxl or XlsxWriter to export Excel."]}).to_csv(index=False).encode("utf-8")

    with pd.ExcelWriter(output, engine=engine) as writer:
        wrote_any = False
        used_names = set()

        for name, frame in (sheets or {}).items():
            df = frame if frame is not None else pd.DataFrame()
            safe_name = _safe_sheet_name(str(name), used_names)
            # Always write—empty frames still create a visible sheet
            df.to_excel(writer, sheet_name=safe_name, index=False)
            wrote_any = True

        # Guarantee at least one visible sheet
        if not wrote_any:
            pd.DataFrame({"Info": ["No data available in this export window."]}).to_excel(
                writer, sheet_name="Summary", index=False
            )

    return output.getvalue()

def _compute_risk(df: pd.DataFrame) -> pd.Series:
    needed = {"stress_level","anxiety_level","depression_level"}
    if not needed.issubset(df.columns):
        return pd.Series(index=df.index, dtype=float)
    comp = df[list(needed)].apply(pd.to_numeric, errors="coerce")
    return (comp["stress_level"]*0.45 + comp["anxiety_level"]*0.35 + comp["depression_level"]*0.20).clip(0,10)


def _risk_bucket(series: pd.Series) -> pd.Series:
    return pd.cut(series, bins=[-0.001,4,7,10], labels=["Low","Moderate","High"])  # aligned to app


def _spark_area(s: pd.Series, title: str) -> Optional[go.Figure]:
    if s is None or len(s) == 0:
        return None
    df = s.rename_axis("date").reset_index(name="value")
    fig = px.area(df, x="date", y="value", title=title)
    fig.update_layout(height=160, margin=dict(l=20,r=20,t=40,b=20))
    fig.update_yaxes(rangemode="tozero")
    return fig


def _kpi_card(label: str, value: str, sub: Optional[str] = None):
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.9rem;color:#64748b'>{label}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:2.2rem;font-weight:800;line-height:1'>{value}</div>", unsafe_allow_html=True)
        if sub:
            st.caption(sub)

# ----------------- Auth / Session -----------------


def _role_guard():
    # Optional role check (non-breaking): only warn if not admin
    role = st.session_state.get("role", "admin")
    if role != "admin":
        st.warning("You do not appear to be an admin. Some features may be hidden or read-only.")

# ----------------- Main -----------------

def admin_dashboard():
    # HERO
    st.markdown("<div class='mp-hero'><h1>🧰 MindPulse Admin Studio</h1><p>Manage users, data and insights with a friendly, visual console.</p></div>", unsafe_allow_html=True)
    # _logout_button()
    _role_guard()
    st.markdown("---")

    # === Sidebar Filters & Actions ===
    with st.sidebar:
        st.subheader("Filters & Actions")
        refresh = st.button("🔄 Refresh data")
        if refresh:
            _safe_load_users.clear(); _safe_load_inputs.clear(); _safe_load_psych.clear(); _safe_load_feedback.clear()
            st.toast("Data refreshed")
        # Global date filter for inputs/feedback analytics
        default_from = date.today() - timedelta(days=30)
        date_from = st.date_input("From", value=default_from)
        date_to = st.date_input("To", value=date.today())
        risk_min = st.slider("Min risk threshold (alerts)", 0.0, 10.0, 7.0, 0.5)
        st.caption("Risk uses same weights as the user app.")

    # Load data
    users_df = _safe_load_users()
    inputs_df = _safe_load_inputs()
    psych_df  = _safe_load_psych()
    feedback_df = _safe_load_feedback()

    # Apply sidebar date filter to inputs/feedback views
    def _date_slice(df: pd.DataFrame, tcol: str) -> pd.DataFrame:
        if df is None or df.empty or tcol not in df.columns:
            return df
        d = df.copy()
        d = d.dropna(subset=[tcol])
        d = d[(d[tcol].dt.date >= date_from) & (d[tcol].dt.date <= date_to)]
        return d

    inputs_win = _date_slice(inputs_df, "timestamp")
    feedback_win = _date_slice(feedback_df, "timestamp")

    # === KPIs ===
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _kpi_card("Registered Users", f"{len(users_df):,}")
        st.markdown("------")
    with c2:
        _kpi_card("Submissions (window)", f"{len(inputs_win):,}", f"{date_from} → {date_to}")
        st.markdown("-----")
    with c3:
        avg_risk = None
        if not inputs_win.empty:
            r = _compute_risk(inputs_win)
            if not r.dropna().empty:
                avg_risk = round(r.mean(), 2)
        _kpi_card("Avg Risk", f"{avg_risk if avg_risk is not None else '—'}", "windowed")
        st.markdown("-----")
    with c4:
        _kpi_card("Feedback (window)", f"{len(feedback_win):,}")
        st.markdown("-----")

    # KPI Sparklines
    colsp1, colsp2 = st.columns(2)
    with colsp1:
        # submissions per day spark
        if not inputs_win.empty and "timestamp" in inputs_win.columns:
            s = inputs_win.dropna(subset=["timestamp"]).timestamp.dt.date.value_counts().sort_index()
            fig = _spark_area(s, "Submissions per day")
            if fig: st.plotly_chart(fig, use_container_width=True)
    with colsp2:
        # average risk per day spark
        if not inputs_win.empty and "timestamp" in inputs_win.columns:
            tmp = inputs_win.dropna(subset=["timestamp"]).copy()
            tmp["date"] = tmp["timestamp"].dt.date
            tmp["risk"] = _compute_risk(tmp)
            g = tmp.groupby("date")["risk"].mean().round(2)
            fig = _spark_area(g, "Avg risk per day")
            if fig: st.plotly_chart(fig, use_container_width=True)

    # === NAV ===
    tabs = st.tabs(["Users", "User Inputs", "Psychologists", "Feedback", "Analytics", "Exports"])

    # USERS
    with tabs[0]:
        st.header("👥 Registered Users")
        if users_df.empty:
            st.info("No users found.")
        else:
            fcol1, fcol2 = st.columns([2,1])
            with fcol1:
                q = st.text_input("Search (name or email)")
            with fcol2:
                edit = st.toggle("Inline edit", value=False)
            df = users_df.copy()
            if q:
                mask = pd.Series(False, index=df.index)
                for col in [c for c in df.columns if c.lower() in ("name","email")]:
                    mask = mask | df[col].astype(str).str.contains(q, case=False, na=False)
                df = df[mask]
            if edit:
                edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
                if st.button("💾 Save Users", type="primary"):
                    try:
                        save_users(edited)
                        st.success("Users updated.")
                        st.balloons(); _safe_load_users.clear()
                    except Exception as e:
                        st.error(e)
            else:
                st.dataframe(df, use_container_width=True)
            st.download_button("Download Users CSV", _csv_bytes(df), file_name="users.csv", mime="text/csv")
            up = st.file_uploader("Upload Updated Users CSV", type=["csv"], key="users_upload")
            if up:
                try:
                    new_df = pd.read_csv(up)
                    save_users(new_df); _safe_load_users.clear()
                    st.success("✅ Users updated successfully!")
                except Exception as e:
                    st.error(e)

    # USER INPUTS
    # USER INPUTS (enhanced: inline edit + row-level fallback + backups + audit)
    with tabs[1]:
        st.header("🧠 User Mental Health Data (editable)")
        if inputs_df.empty:
            st.info("No user inputs found.")
        else:
            # Filters (same semantics as before)
            cfil1, cfil2, cfil3 = st.columns(3)
            with cfil1:
                email_filter = st.text_input("Email contains…")
            with cfil2:
                min_sleep = st.slider("Min sleep (hrs)", 0, 12, 0)
            with cfil3:
                max_sleep = st.slider("Max sleep (hrs)", 0, 12, 12)

            df = inputs_win.copy()
            if email_filter and "email" in df.columns:
                df = df[df["email"].astype(str).str.contains(email_filter, case=False, na=False)]
            if "sleep_hours" in df.columns:
                df = df[(df["sleep_hours"] >= min_sleep) & (df["sleep_hours"] <= max_sleep)]

            st.markdown("**Preview (windowed)**")
            st.dataframe(df, use_container_width=True)

            # Exports / uploads (unchanged)
            st.download_button("Download User Inputs CSV", _csv_bytes(df), file_name="user_inputs.csv", mime="text/csv")
            up2 = st.file_uploader("Upload Updated User Inputs CSV", type=["csv"], key="user_inputs_upload")
            if up2:
                try:
                    new_inputs_df = pd.read_csv(up2)
                    # backup existing before overwrite
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.session_state.setdefault("admin_user_inputs_backups", {})[ts] = _csv_bytes(inputs_df)
                    save_user_inputs(new_inputs_df); _safe_load_inputs.clear()
                    st.success("✅ User inputs updated successfully (from uploaded CSV)!")
                except Exception as e:
                    st.error(e)

            st.markdown("---")
            st.subheader("Admin edit / update / delete")
            st.caption("You can edit the whole table inline (best), or edit/delete a single row below (fallback). Backups are created automatically before saves.")

            # Prepare audit log structure in session
            if "admin_user_inputs_audit" not in st.session_state:
                st.session_state["admin_user_inputs_audit"] = []  # list of dicts: {when, actor, action, details}

            # Create a backup helper (store last backup bytes in session so admin can restore/download)
            def _store_backup(bytes_blob: bytes, note: str = ""):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.session_state.setdefault("admin_user_inputs_backups", {})[ts] = bytes_blob
                st.session_state.setdefault("admin_user_inputs_last_backup_note", {})[ts] = note
                return ts

            # Inline editor (preferred) — only if data editor exists
            editor_supported = hasattr(st, "data_editor") or hasattr(st, "experimental_data_editor")
            if editor_supported:
                st.markdown("**Inline table editor (recommended)**")
                try:
                    # Use newer name if available
                    if hasattr(st, "data_editor"):
                        edited = st.data_editor(df, num_rows="dynamic")
                    else:
                        edited = st.experimental_data_editor(df, num_rows="dynamic")
                    if st.button("💾 Save edited table", key="save_edited_table"):
                        try:
                            # Save backup of current stored inputs (not the filtered df)
                            b = _csv_bytes(inputs_df)
                            backup_ts = _store_backup(b, note="Before inline save")
                            actor = st.session_state.get("name", "admin")
                            st.session_state["admin_user_inputs_audit"].append({
                                "when": datetime.now().isoformat(),
                                "actor": actor,
                                "action": "save_table",
                                "details": f"Inline save; backup_ts={backup_ts}; rows_before={len(inputs_df)} rows_after={len(edited)}",
                            })
                            # Persist edited — note: edited may be filtered subset; prefer to save the full edited as-is
                            save_user_inputs(edited)
                            _safe_load_inputs.clear()
                            st.success("✅ All edits saved.")
                            # st.experimental_rerun()
                        except Exception as e:
                            st.error("Couldn't save edits.")
                            st.exception(e)
                except Exception as e:
                    st.info("Inline editor not available in this Streamlit version — falling back to row-level editor.")
                    st.exception(e)
                    editor_supported = False

            # Fallback: row-level edit / delete (safe)
            if not editor_supported:
                st.markdown("**Row-level edit & delete (fallback)**")
                working_df = inputs_df.reset_index(drop=False).rename(columns={"index": "_orig_index"})
                if working_df.empty:
                    st.info("No submissions to edit.")
                else:
                    # build readable labels
                    def _label_row(r):
                        email = r.get("email", "")
                        when = r.get("timestamp", "")
                        who = str(email)[:32] if email else str(r.get("_orig_index"))
                        return f"{r.get('_orig_index')} — {who} @ {when}"

                    labels = [ _label_row(working_df.iloc[i]) for i in range(len(working_df)) ]
                    sel = st.selectbox("Select submission to edit or delete", options=list(range(len(working_df))), format_func=lambda i: labels[i], key="select_input_row")

                    row = working_df.iloc[sel]
                    st.markdown("### Selected submission (read-only preview)")
                    st.json(row.to_dict())

                    st.markdown("### Edit fields")
                    # choose editable fields (extend as needed)
                    e_email = st.text_input("Email", value=str(_safe_get(row, "email", "")), key="edit_email")
                    e_name = st.text_input("Name", value=str(_safe_get(row, "name", "")), key="edit_name")
                    e_timestamp = st.text_input("Timestamp", value=str(_safe_get(row, "timestamp", "")), key="edit_ts")
                    e_stress = st.number_input("Stress (0-10)", min_value=0.0, max_value=10.0, value=float(_safe_get(row, "stress_level", 0)), step=0.1, key="edit_stress")
                    e_anxiety = st.number_input("Anxiety (0-10)", min_value=0.0, max_value=10.0, value=float(_safe_get(row, "anxiety_level", 0)), step=0.1, key="edit_anx")
                    e_depression = st.number_input("Depression (0-10)", min_value=0.0, max_value=10.0, value=float(_safe_get(row, "depression_level", 0)), step=0.1, key="edit_dep")
                    e_sleep = st.number_input("Sleep hours", min_value=0.0, max_value=24.0, value=float(_safe_get(row, "sleep_hours", 0)), step=0.1, key="edit_sleep")

                    col_save, col_delete = st.columns([1,1])
                    with col_save:
                        if st.button("💾 Save changes to this submission", key=f"save_row_{sel}"):
                            try:
                                idx = int(row["_orig_index"])
                                df_copy = inputs_df.copy()
                                # backup before change
                                backup_ts = _store_backup(_csv_bytes(inputs_df), note=f"Row-edit before idx={idx}")
                                # apply updates if columns exist
                                if "email" in df_copy.columns: df_copy.loc[idx, "email"] = e_email
                                if "name" in df_copy.columns: df_copy.loc[idx, "name"] = e_name
                                if "timestamp" in df_copy.columns:
                                    try:
                                        df_copy.loc[idx, "timestamp"] = pd.to_datetime(e_timestamp)
                                    except Exception:
                                        df_copy.loc[idx, "timestamp"] = e_timestamp
                                if "stress_level" in df_copy.columns: df_copy.loc[idx, "stress_level"] = float(e_stress)
                                if "anxiety_level" in df_copy.columns: df_copy.loc[idx, "anxiety_level"] = float(e_anxiety)
                                if "depression_level" in df_copy.columns: df_copy.loc[idx, "depression_level"] = float(e_depression)
                                if "sleep_hours" in df_copy.columns: df_copy.loc[idx, "sleep_hours"] = float(e_sleep)
                                # record audit
                                actor = st.session_state.get("name", "admin")
                                st.session_state["admin_user_inputs_audit"].append({
                                    "when": datetime.now().isoformat(),
                                    "actor": actor,
                                    "action": "edit_row",
                                    "details": f"idx={idx}; backup_ts={backup_ts}",
                                })
                                # persist
                                save_user_inputs(df_copy)
                                _safe_load_inputs.clear()
                                st.success("✅ Submission updated.")
                                # st.experimental_rerun()
                            except Exception as e:
                                st.error("Failed to update submission.")
                                st.exception(e)

                    with col_delete:
                        confirm = st.checkbox("Confirm delete", key=f"confirm_delete_{sel}")
                        if st.button("🗑️ Delete this submission", key=f"delete_row_{sel}"):
                            if not confirm:
                                st.warning("Please check 'Confirm delete' to enable deletion.")
                            else:
                                try:
                                    idx = int(row["_orig_index"])
                                    # backup
                                    backup_ts = _store_backup(_csv_bytes(inputs_df), note=f"Before delete idx={idx}")
                                    df_copy = inputs_df.copy().drop(index=idx).reset_index(drop=True)
                                    # audit
                                    actor = st.session_state.get("name", "admin")
                                    st.session_state["admin_user_inputs_audit"].append({
                                        "when": datetime.now().isoformat(),
                                        "actor": actor,
                                        "action": "delete_row",
                                        "details": f"idx={idx}; backup_ts={backup_ts}",
                                    })
                                    save_user_inputs(df_copy)
                                    _safe_load_inputs.clear()
                                    st.success("✅ Submission deleted.")
                                    # st.experimental_rerun()
                                except Exception as e:
                                    st.error("Failed to delete submission.")
                                    st.exception(e)

            # Show last backup download and audit log
            st.markdown("---")
            backups = st.session_state.get("admin_user_inputs_backups", {})
            if backups:
                last_ts = sorted(backups.keys())[-1]
                st.markdown(f"**Last backup:** {last_ts} — {st.session_state.get('admin_user_inputs_last_backup_note', {}).get(last_ts, '')}")
                st.download_button("Download last backup", data=backups[last_ts], file_name=f"user_inputs_backup_{last_ts}.csv", mime="text/csv")
            else:
                st.caption("No backups created during this admin session yet. Backups are created whenever you save or delete entries.")

            # Audit trail preview
            st.markdown("**Audit trail (session)**")
            audit = st.session_state.get("admin_user_inputs_audit", [])
            if audit:
                st.table(pd.DataFrame(audit).sort_values("when", ascending=False).reset_index(drop=True))
            else:
                st.caption("No audit entries recorded in this session yet.")

            st.markdown("---")
            st.caption("Editing here changes production user_inputs storage. Consider downloading a backup before bulk edits.")

    # PSYCHOLOGISTS
    with tabs[2]:
        st.header("🩺 Psychologists & Counsellors")
        if psych_df.empty:
            st.info("No psychologists found.")
        else:
            pcol1, pcol2 = st.columns([2,1])
            with pcol1:
                st.dataframe(psych_df, use_container_width=True)
            with pcol2:
                st.download_button("Download Psychologists CSV", _csv_bytes(psych_df), file_name="psychologists.csv", mime="text/csv")
            uploaded_psych = st.file_uploader("Upload Updated Psychologists CSV", type=["csv"], key="psych_upload")
            if uploaded_psych:
                try:
                    new_psych_df = pd.read_csv(uploaded_psych)
                    save_psychologists(new_psych_df); _safe_load_psych.clear()
                    st.success("✅ Psychologists updated successfully!")
                except Exception as e:
                    st.error(e)

        st.subheader("➕ Add a Psychologist")
        with st.form("add_psych_form", clear_on_submit=True):
            name = st.text_input("Name")
            specialization = st.text_input("Specialization")
            emailp = st.text_input("Email")
            phone = st.text_input("Phone")
            booking = st.text_input("Booking URL (optional)")
            submitted = st.form_submit_button("Add Psychologist")
            if submitted:
                if name and specialization and emailp and phone:
                    try:
                        append_psychologist({
                            "name": name,
                            "specialty": specialization,
                            "email": emailp,
                            "phone": phone,
                            "booking_url": booking,
                        })
                        st.success(f"✅ {name} added successfully!")
                        st.balloons(); _safe_load_psych.clear()
                    except Exception as e:
                        st.error(e)
                else:
                    st.warning("Please fill all required fields.")

    # FEEDBACK
    with tabs[3]:
        st.header("💬 User Feedback")
        if feedback_df.empty:
            st.info("No feedback yet.")
        else:
            st.dataframe(feedback_win, use_container_width=True)
            st.download_button("Download Feedback CSV", _csv_bytes(feedback_win), file_name="user_feedback.csv", mime="text/csv")

            fcol1, fcol2 = st.columns(2)
            with fcol1:
                if "rating" in feedback_win.columns:
                    fig = px.histogram(feedback_win.dropna(subset=["rating"]), x="rating", nbins=5, title="Ratings distribution")
                    fig.update_xaxes(dtick=1, range=[0.5,5.5])
                    st.plotly_chart(fig, use_container_width=True)
            with fcol2:
                if "timestamp" in feedback_win.columns:
                    d = feedback_win.dropna(subset=["timestamp"]).assign(date=lambda d: d["timestamp"].dt.date)
                    vol = d.groupby("date").size().reset_index(name="feedback")
                    if not vol.empty:
                        st.plotly_chart(px.area(vol, x="date", y="feedback", markers=True, title="Feedback volume"), use_container_width=True)

            if st.button("🗑 Clear All Feedback", type="secondary"):
                clear_feedback(); _safe_load_feedback.clear()
                st.success("✅ All feedback cleared.")

    # ANALYTICS
    with tabs[4]:
        st.header("📈 Analytics & Insights")
        # Risk mix over time (stacked area by share)
        if not inputs_win.empty and "timestamp" in inputs_win.columns:
            df = inputs_win.dropna(subset=["timestamp"]).copy()
            df["date"] = df["timestamp"].dt.date
            df["risk"] = _compute_risk(df)
            df["bucket"] = _risk_bucket(df["risk"]).astype(str)
            grp = df.groupby(["date","bucket"]).size().rename("count").reset_index()
            totals = grp.groupby("date")["count"].transform("sum")
            grp["pct"] = (grp["count"] / totals * 100).round(1)

            a1, a2 = st.columns(2)
            with a1:
                fig_mix = px.area(grp, x="date", y="pct", color="bucket",
                                  title="Risk mix over time (% of submissions)",
                                  labels={"pct":"%","bucket":"Risk"})
                fig_mix.update_yaxes(range=[0,100])
                st.plotly_chart(fig_mix, use_container_width=True)

            with a2:
                # Submission timing heatmap (weekday x hour)
                timing = df.copy()
                timing["weekday"] = timing["timestamp"].dt.day_name()
                timing["hour"] = timing["timestamp"].dt.hour
                pivot = timing.pivot_table(index="weekday", columns="hour", values="email" if "email" in timing.columns else "date", aggfunc="count").fillna(0)
                # Reorder weekdays
                order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                pivot = pivot.reindex(order)
                fig_heat = px.imshow(pivot, aspect="auto", title="Submission timing heatmap",
                                     labels=dict(x="Hour", y="Weekday", color="Submissions"))
                st.plotly_chart(fig_heat, use_container_width=True)

            st.subheader("⚠️ High‑risk alerts (last 7 days)")
            recent = inputs_df.copy()
            if not recent.empty and "timestamp" in recent.columns:
                recent = recent.dropna(subset=["timestamp"]).copy()
                recent["risk"] = _compute_risk(recent)
                cutoff = datetime.now() - timedelta(days=7)
                alerts = recent[(recent["timestamp"] >= cutoff) & (recent["risk"] >= risk_min)]
                show_cols = [c for c in ["timestamp","email","name","risk","stress_level","anxiety_level","depression_level","sleep_hours"] if c in alerts.columns]
                st.dataframe(alerts.sort_values("risk", ascending=False)[show_cols].head(50), use_container_width=True)
                st.caption("Showing up to 50 most recent high‑risk submissions. Adjust threshold in the sidebar.")
            else:
                st.info("No timestamped inputs to compute alerts.")

            st.subheader("🏅 Top at‑risk users (avg risk in last 30 days)")
            last30 = inputs_df.copy()
            if not last30.empty and "timestamp" in last30.columns:
                last30 = last30.dropna(subset=["timestamp"]).copy()
                last30 = last30[last30["timestamp"] >= (datetime.now() - timedelta(days=30))]
                last30["risk"] = _compute_risk(last30)
                key = "email" if "email" in last30.columns else ("name" if "name" in last30.columns else None)
                if key:
                    agg = last30.groupby(key)["risk"].mean().round(2).sort_values(ascending=False).reset_index()
                    agg.rename(columns={key:"User", "risk":"Avg Risk"}, inplace=True)
                    st.dataframe(agg.head(25), use_container_width=True)
                else:
                    st.caption("No email/name column to aggregate by user.")
            else:
                st.info("Not enough recent data for ranking.")
        else:
            st.info("No inputs in selected window.")

    # EXPORTS
    with tabs[5]:
        st.header("📦 Exports")
        st.markdown("Download individual CSVs from each tab, or package everything into one Excel workbook.")
        pack = _excel_pack({
            "Users": users_df,
            "UserInputs": inputs_df,
            "Psychologists": psych_df,
            "Feedback": feedback_df,
        })
        st.download_button("Download All (Excel)", data=pack, file_name=f"mindpulse_export_{datetime.now():%Y%m%d_%H%M%S}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("---")
    st.caption("MindPulse Admin Studio • Visual, friendly, and fast. All analytics adapt to your data in real time.")
