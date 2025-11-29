# utils/user_utils.py
import os
import pandas as pd
from datetime import datetime

USER_INPUTS_FILE = os.path.join("data", "user_inputs.csv")
FEEDBACK_FILE = os.path.join("data", "user_feedback.csv")

def init_files():
    """Create data folder and CSVs with headers if not present."""
    os.makedirs("data", exist_ok=True)

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

    if not os.path.exists(FEEDBACK_FILE):
        pd.DataFrame(columns=["timestamp", "email", "name", "rating", "feedback"]).to_csv(FEEDBACK_FILE, index=False)

def save_user_inputs(form_data: dict, email: str = None, name: str = None):
    init_files()

    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "email": email or form_data.get("email", ""),
        "name": name or form_data.get("name", ""),
        "age": form_data.get("age"),
        "gender": form_data.get("gender"),
        "occupation": form_data.get("occupation"),
        "sleep_hours": form_data.get("sleep_hours"),
        "exercise_freq": form_data.get("exercise_freq"),
        "diet_quality": form_data.get("diet_quality"),
        "stress_level": form_data.get("stress_level"),
        "anxiety_level": form_data.get("anxiety_level"),
        "depression_level": form_data.get("depression_level"),
        "social_interaction": form_data.get("social_interaction"),
        "work_life_balance": form_data.get("work_life_balance"),
        "coping_methods": form_data.get("coping_methods"),
        "past_mental_illness": form_data.get("past_mental_illness"),
        "current_medication": form_data.get("current_medication"),
        "medication_details": form_data.get("medication_details"),
        "feedback": form_data.get("feedback", "")
    }

    df = pd.read_csv(USER_INPUTS_FILE)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(USER_INPUTS_FILE, index=False)

def save_feedback(email: str, name: str, rating: int, feedback_text: str):
    """Append feedback to feedback CSV and also a short entry in user_inputs feedback column (optional)."""
    init_files()
    fb_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "email": email or "",
        "name": name or "",
        "rating": rating,
        "feedback": feedback_text
    }
    fb_df = pd.read_csv(FEEDBACK_FILE)
    fb_df = pd.concat([fb_df, pd.DataFrame([fb_row])], ignore_index=True)
    fb_df.to_csv(FEEDBACK_FILE, index=False)

    # Optionally also append the feedback summary to the user_inputs file for cross reference
    # try:
    #     inputs_df = pd.read_csv(USER_INPUTS_FILE)
    #     # Keep a lightweight feedback log in user_inputs (timestamp, email, feedback)
    #     inputs_df = pd.concat([inputs_df, pd.DataFrame([{
    #         "timestamp": fb_row["timestamp"],
    #         "email": fb_row["email"],
    #         "name": fb_row["name"],
    #         "feedback": fb_row["feedback"]
    #     }])], ignore_index=True)
    #     # Save back without breaking structure (missing columns will be NaN)
    #     inputs_df.to_csv(USER_INPUTS_FILE, index=False)
    # except Exception:
    #     # if anything goes wrong updating user_inputs, ignore (feedback still saved)
    #     pass
