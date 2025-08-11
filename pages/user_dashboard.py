import streamlit as st
import csv
import os
from utils.form_fields import mental_health_form
from utils.analysis import analyze_mental_health, radar_chart, pie_chart, line_chart, random_psychologists
from utils.extra_visuals import bar_chart, gauge_chart, stacked_area_chart, histogram_sleep

USER_INPUTS_FILE = os.path.join("data", "user_inputs.csv")

def init_user_inputs_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(USER_INPUTS_FILE):
        with open(USER_INPUTS_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "email", "name", "age", "gender", "occupation", 
                "sleep_hours", "exercise_freq", "diet_quality",
                "stress_level", "anxiety_level", "depression_level",
                "social_interaction", "work_life_balance", "coping_methods",
                "past_mental_illness", "current_medication", "medication_details"
            ])

def save_form_data(email, name, form_data):
    with open(USER_INPUTS_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            email, name, form_data["age"], form_data["gender"], form_data["occupation"],
            form_data["sleep_hours"], form_data["exercise_freq"], form_data["diet_quality"],
            form_data["stress_level"], form_data["anxiety_level"], form_data["depression_level"],
            form_data["social_interaction"], form_data["work_life_balance"], form_data["coping_methods"],
            form_data["past_mental_illness"], form_data["current_medication"], form_data["medication_details"]
        ])

def user_dashboard():
    st.title(f"👋 Welcome, {st.session_state.name}")
    st.write("Please fill out the following mental health assessment form.")

    init_user_inputs_file()
    form_data = mental_health_form()

    if form_data:
        save_form_data(st.session_state.email, st.session_state.name, form_data)
        
        st.success("✅ Your responses have been recorded successfully!")
        
        # --- Analysis ---
        analysis_result = analyze_mental_health(form_data)
        st.subheader("📊 Analysis Report")
        st.write(f"**Risk Level:** {analysis_result['risk_level']}")
        st.write(f"**Overall Score:** {analysis_result['score']} / 10")
        
        # --- Visualizations ---
        st.plotly_chart(radar_chart(form_data))
        st.plotly_chart(pie_chart(form_data))
        st.plotly_chart(line_chart(form_data))
        st.plotly_chart(bar_chart(form_data))
        st.plotly_chart(gauge_chart(analysis_result['score']))
        st.plotly_chart(stacked_area_chart(form_data))
        st.plotly_chart(histogram_sleep(form_data))
        
        # --- Psychologist Suggestions ---
        st.subheader("🩺 Suggested Psychologists & Counsellors")
        for prof in random_psychologists():
            st.write(f"**{prof['name']}**")
            st.write(f"📧 {prof['email']}")
            st.write(f"📞 {prof['phone']}")
            st.markdown("---")
