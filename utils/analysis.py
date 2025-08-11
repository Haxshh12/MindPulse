import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- Simulated ML prediction ---
def analyze_mental_health(form_data):
    """Fake analysis logic — replace with ML model later."""
    # Weighted average score
    score = (
        form_data["stress_level"] * 0.4 +
        form_data["anxiety_level"] * 0.3 +
        form_data["depression_level"] * 0.3
    )

    risk_level = "Low"
    if score > 7:
        risk_level = "High"
    elif score > 4:
        risk_level = "Moderate"

    return {
        "score": round(score, 2),
        "risk_level": risk_level
    }

# --- Visualization functions ---
def radar_chart(form_data):
    categories = ["Stress", "Anxiety", "Depression", "Sleep", "Exercise", "Diet"]
    values = [
        form_data["stress_level"],
        form_data["anxiety_level"],
        form_data["depression_level"],
        form_data["sleep_hours"],
        {"Never": 0, "Rarely": 2, "Sometimes": 5, "Often": 7, "Daily": 10}[form_data["exercise_freq"]],
        {"Poor": 2, "Average": 5, "Good": 8}[form_data["diet_quality"]]
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Your Profile'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=False
    )
    return fig

def pie_chart(form_data):
    labels = ["Stress", "Anxiety", "Depression"]
    values = [form_data["stress_level"], form_data["anxiety_level"], form_data["depression_level"]]
    fig = px.pie(names=labels, values=values, title="Mental Health Distribution")
    return fig

def line_chart(form_data):
    df = pd.DataFrame({
        "Category": ["Stress", "Anxiety", "Depression"],
        "Score": [form_data["stress_level"], form_data["anxiety_level"], form_data["depression_level"]]
    })
    fig = px.line(df, x="Category", y="Score", markers=True, title="Mood Levels")
    return fig

# --- Suggestion Generator ---
def random_psychologists():
    professionals = [
        {"name": "Dr. Ayesha Khan", "email": "ayesha.khan@example.com", "phone": "+91 98765 43210"},
        {"name": "Dr. Rajiv Mehta", "email": "rajiv.mehta@example.com", "phone": "+91 99887 66554"},
        {"name": "Dr. Priya Sharma", "email": "priya.sharma@example.com", "phone": "+91 98123 45678"},
        {"name": "Dr. Arjun Nair", "email": "arjun.nair@example.com", "phone": "+91 91234 56789"},
    ]
    return random.sample(professionals, 2)
