# utils/admin_utils.py
import os
import pandas as pd

# Paths (keep consistent with other utils)
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
USER_INPUTS_FILE = os.path.join(DATA_DIR, "user_inputs.csv")
PSYCH_FILE = os.path.join(DATA_DIR, "psychologists.csv")
FEEDBACK_FILE = os.path.join(DATA_DIR, "user_feedback.csv")  # same as user_utils

def init_files():
    """Create data folder and CSVs with sensible headers if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=["email", "password", "role", "name"]).to_csv(USERS_FILE, index=False)

    if not os.path.exists(USER_INPUTS_FILE):
        cols = [
            "timestamp", "email", "name", "age", "gender", "occupation",
            "sleep_hours", "exercise_freq", "diet_quality",
            "stress_level", "anxiety_level", "depression_level",
            "social_interaction", "work_life_balance", "coping_methods",
            "past_mental_illness", "current_medication", "medication_details",
            "feedback"
        ]
        pd.DataFrame(columns=cols).to_csv(USER_INPUTS_FILE, index=False)

    if not os.path.exists(PSYCH_FILE):
        # Sample psychologists — admin can edit later
        sample = [
            {"name": "Dr. Ayesha Khan", "specialization": "Clinical Psychologist", "email": "ayesha.khan@example.com", "phone": "+91 98765 43210"},
            {"name": "Dr. Rajiv Mehta", "specialization": "Counseling Psychologist", "email": "rajiv.mehta@example.com", "phone": "+91 99887 66554"},
        ]
        pd.DataFrame(sample).to_csv(PSYCH_FILE, index=False)

    if not os.path.exists(FEEDBACK_FILE):
        pd.DataFrame(columns=["timestamp", "email", "name", "rating", "feedback"]).to_csv(FEEDBACK_FILE, index=False)

# ----------------- Loaders & Savers -----------------
def load_users():
    init_files()
    try:
        return pd.read_csv(USERS_FILE)
    except Exception:
        return pd.DataFrame(columns=["email", "password", "role", "name"])

def save_users(df: pd.DataFrame):
    init_files()
    df.to_csv(USERS_FILE, index=False)

def load_user_inputs():
    init_files()
    try:
        return pd.read_csv(USER_INPUTS_FILE)
    except Exception:
        return pd.DataFrame(columns=[
            "timestamp", "email", "name", "age", "gender", "occupation",
            "sleep_hours", "exercise_freq", "diet_quality",
            "stress_level", "anxiety_level", "depression_level",
            "social_interaction", "work_life_balance", "coping_methods",
            "past_mental_illness", "current_medication", "medication_details",
            "feedback"
        ])

def save_user_inputs(df: pd.DataFrame):
    init_files()
    df.to_csv(USER_INPUTS_FILE, index=False)

def load_psychologists():
    init_files()
    try:
        return pd.read_csv(PSYCH_FILE)
    except Exception:
        return pd.DataFrame(columns=["name", "specialization", "email", "phone"])

def save_psychologists(df: pd.DataFrame):
    init_files()
    df.to_csv(PSYCH_FILE, index=False)

def append_psychologist(record: dict):
    """Append a single psychologist record (dict with keys name,specialization,email,phone)."""
    init_files()
    df = load_psychologists()
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    save_psychologists(df)

def load_feedback():
    init_files()
    try:
        return pd.read_csv(FEEDBACK_FILE)
    except Exception:
        return pd.DataFrame(columns=["timestamp", "email", "name", "rating", "feedback"])

def save_feedback(df: pd.DataFrame):
    init_files()
    df.to_csv(FEEDBACK_FILE, index=False)

def append_feedback(record: dict):
    """Append a single feedback record (dict with keys timestamp,email,name,rating,feedback)."""
    init_files()
    df = load_feedback()
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    save_feedback(df)

def clear_feedback():
    """Remove all feedback entries (admin action)."""
    init_files()
    pd.DataFrame(columns=["timestamp", "email", "name", "rating", "feedback"]).to_csv(FEEDBACK_FILE, index=False)
