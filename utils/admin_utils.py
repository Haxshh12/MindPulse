import csv
import os
import pandas as pd

USERS_FILE = os.path.join("data", "users.csv")
USER_INPUTS_FILE = os.path.join("data", "user_inputs.csv")
PSYCH_FILE = os.path.join("data", "psychologists.csv")

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    else:
        return pd.DataFrame(columns=["email", "password", "role", "name"])

def load_user_inputs():
    if os.path.exists(USER_INPUTS_FILE):
        return pd.read_csv(USER_INPUTS_FILE)
    else:
        return pd.DataFrame(columns=[
            "timestamp", "email", "name", "age", "gender", "marital_status", "employment", "living",
            "family_history", "mood_swings", "anxiety", "depression", "sleep", "exercise",
            "screen_time", "addictions", "work", "social", "overthinking", "memory"
        ])

def load_psychologists():
    if os.path.exists(PSYCH_FILE):
        return pd.read_csv(PSYCH_FILE)
    else:
        # create default sample psychologists
        df = pd.DataFrame([
            {"name": "Dr. Ayesha Khan", "email": "ayesha.khan@example.com", "phone": "+91 98765 43210"},
            {"name": "Dr. Rajiv Mehta", "email": "rajiv.mehta@example.com", "phone": "+91 99887 66554"},
        ])
        df.to_csv(PSYCH_FILE, index=False)
        return df

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def save_user_inputs(df):
    df.to_csv(USER_INPUTS_FILE, index=False)

def save_psychologists(df):
    df.to_csv(PSYCH_FILE, index=False)
