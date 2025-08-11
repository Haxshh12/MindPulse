import streamlit as st

def mental_health_form():
    """Render a clean, minimal, interactive mental health form."""
    st.header("📝 Mental Health Self-Assessment Form")

    with st.form("mh_form"):
        # --- Basic Info ---
        st.subheader("Personal Information")
        age = st.slider("Age", 13, 100, 25)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        occupation = st.text_input("Occupation", placeholder="e.g., Student, Engineer")

        # --- Lifestyle ---
        st.subheader("Lifestyle & Habits")
        sleep_hours = st.slider("Average Sleep Hours per Night", 0, 12, 7)
        exercise_freq = st.selectbox("Exercise Frequency", ["Never", "Rarely", "Sometimes", "Often", "Daily"])
        diet_quality = st.radio("Diet Quality", ["Poor", "Average", "Good"])

        # --- Mental Health Indicators ---
        st.subheader("Mental Health Indicators")
        stress_level = st.slider("Stress Level", 0, 10, 5)
        anxiety_level = st.slider("Anxiety Level", 0, 10, 4)
        depression_level = st.slider("Depression Level", 0, 10, 3)

        social_interaction = st.selectbox("Social Interaction Frequency", ["Rarely", "Occasionally", "Weekly", "Daily"])
        work_life_balance = st.radio("Work-Life Balance", ["Poor", "Average", "Good"])

        # --- Conditional Question ---
        if stress_level > 7 or anxiety_level > 7:
            coping_methods = st.text_area("How do you usually cope with stress/anxiety?")
        else:
            coping_methods = "Not Applicable"

        # --- Medical ---
        st.subheader("Medical History")
        past_mental_illness = st.radio("Past Mental Health Diagnosis", ["No", "Yes"])
        current_medication = st.radio("Currently on Medication", ["No", "Yes"])

        if current_medication == "Yes":
            medication_details = st.text_input("Please specify medication")
        else:
            medication_details = "None"

        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        form_data = {
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
            "medication_details": medication_details
        }
        return form_data
    return None
