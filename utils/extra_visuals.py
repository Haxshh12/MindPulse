import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def bar_chart(form_data):
    factors = {
        "Stress": form_data["stress_level"],
        "Anxiety": form_data["anxiety_level"],
        "Depression": form_data["depression_level"],
        "Sleep Quality": form_data["sleep_hours"],
        "Exercise": {"Never": 0, "Rarely": 2, "Sometimes": 5, "Often": 7, "Daily": 10}[form_data["exercise_freq"]],
        "Diet": {"Poor": 2, "Average": 5, "Good": 8}[form_data["diet_quality"]]
    }
    df = pd.DataFrame(list(factors.items()), columns=["Factor", "Score"])
    return px.bar(df, x="Factor", y="Score", title="Wellness Factors Comparison", color="Factor", text="Score")

def gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        delta={'reference': 5},
        gauge={
            'axis': {'range': [0, 10]},
            'steps': [
                {'range': [0, 4], 'color': "green"},
                {'range': [4, 7], 'color': "yellow"},
                {'range': [7, 10], 'color': "red"}
            ],
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': score}
        }
    ))
    fig.update_layout(title="Overall Mental Health Risk Gauge")
    return fig

def stacked_area_chart(form_data):
    df = pd.DataFrame({
        "Factor": ["Stress", "Anxiety", "Depression"],
        "Score": [form_data["stress_level"], form_data["anxiety_level"], form_data["depression_level"]],
        "Day": [1, 1, 1]  # Static for now, can be replaced with time-series data
    })
    return px.area(df, x="Day", y="Score", color="Factor", title="Cumulative Mental Health Factors")

def histogram_sleep(form_data):
    df = pd.DataFrame({"Sleep Hours": [form_data["sleep_hours"]] * 10})  # replicate for visual
    return px.histogram(df, x="Sleep Hours", nbins=5, title="Sleep Hours Distribution")
