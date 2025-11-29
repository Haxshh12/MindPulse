import streamlit as st 
def mental_health_form():
    with st.form("mental_health_form"):
        st.header("📝 Mental Health Self-Assessment")

        # --- Lifestyle Section ---
        st.subheader("Lifestyle")
        age = st.number_input("Age", min_value=10, max_value=100, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
        occupation = st.text_input("Occupation", placeholder="e.g. Student, Engineer, Teacher")
        sleep_hours = st.slider("Average sleep hours per night", 0, 12, 7)
        exercise_freq = st.selectbox("Exercise frequency", ["None", "1-2 days/week", "3-5 days/week", "Daily"])
        diet_quality = st.select_slider("Diet quality", ["Poor", "Average", "Good", "Excellent"])

        # --- Emotional State Section ---
        st.subheader("Emotional & Mental State")
        stress_level = st.slider("Stress level", 1, 10, 5)
        anxiety_level = st.slider("Anxiety level", 1, 10, 5)
        depression_level = st.slider("Depression level", 1, 10, 5)
        social_interaction = st.selectbox("How often do you socialize?", ["Rarely", "Sometimes", "Often"])
        work_life_balance = st.selectbox("Work-life balance", ["Poor", "Fair", "Good", "Excellent"])
        coping_methods = st.multiselect("Coping methods you use", 
                                        ["Meditation", "Exercise", "Hobbies", "Talking to friends/family", "Therapy", "Other"])

        # --- Medical History Section ---
        st.subheader("Medical & Psychological History")
        past_mental_illness = st.radio("Have you been diagnosed with any mental illness in the past?", ["Yes", "No"])
        current_medication = st.radio("Are you currently taking medication for mental health?", ["Yes", "No"])
        medication_details = ""
        if current_medication == "Yes":
            medication_details = st.text_area("Please provide details of your medication")

        submit = st.form_submit_button("Submit Assessment")

    if submit:
        return {
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
            "coping_methods": ", ".join(coping_methods),
            "past_mental_illness": past_mental_illness,
            "current_medication": current_medication,
            "medication_details": medication_details
        }
    return None
