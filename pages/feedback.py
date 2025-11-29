import streamlit as st
import csv
from datetime import datetime
import os

FEEDBACK_FILE = "data/feedback.csv"

def init_feedback_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "email", "name", "rating", "feedback"])  

def feedback_page():
    st.title("📝 User Feedback")
    init_feedback_file()

    # --- SESSION STATE INIT ---
    if "feedback_text" not in st.session_state:
        st.session_state.feedback_text = ""
    if "rating" not in st.session_state:
        st.session_state.rating = 3

    # --- Rating Input (Stars via slider) ---
    rating = st.slider(
        "How would you rate your experience? ⭐",
        1, 5, st.session_state.rating,
        key="rating"
    )

    # --- Feedback Input ---
    feedback = st.text_area(
        "Please share your feedback or suggestions:",
        value=st.session_state.feedback_text,
        key="feedback_text"
    )

    # --- Submit Button ---
    if st.button("✅ Submit Feedback"):
        if not feedback.strip():
            st.error("⚠️ Feedback cannot be empty!")
        else:
            with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    st.session_state.get("email", "anonymous"),
                    st.session_state.get("name", "Guest"),
                    rating,
                    feedback.strip()
                ])
            st.success("🎉 Thank you for your valuable feedback!")

            # Clear after submit
            st.session_state.feedback_text = ""
            st.session_state.rating = 3
            st.experimental_rerun()  # ensures UI resets properly

    # --- Show Past Feedback (user-specific) ---
    st.subheader("📌 Your Previous Feedback")
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            user_feedbacks = [
                row for row in reader 
                if row["email"] == st.session_state.get("email", "")
            ]
            
            if user_feedbacks:
                for fb in reversed(user_feedbacks[-5:]):  # show last 5
                    st.info(f"⭐ {fb['rating']} | {fb['feedback']}  \n🕒 {fb['timestamp']}")
            else:
                st.write("No feedback submitted yet.")
    except Exception as e:
        st.error(f"Error loading feedback history: {e}")
