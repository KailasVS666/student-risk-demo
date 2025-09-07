import streamlit as st
import pandas as pd
import joblib
import os
import google.generativeai as genai

# --------------------
# 1. HELPER FUNCTIONS (Moved to the top)
# --------------------

def generate_llm_advice(risk_level, key_features):
    """Generates a personalized mentoring message using an LLM."""
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if risk_level == 'High':
        tone = "compassionate and urgent"
    elif risk_level == 'Medium':
        tone = "supportive and proactive"
    else:
        tone = "encouraging and motivational"

    prompt = f"""
    You are an empathetic and professional AI student mentor. Your goal is to provide personalized and actionable advice to a student.

    A student's profile has been analyzed, and they have been categorized as having a "{risk_level}" risk level.

    Here are some key factors from their profile:
    - Absences: {key_features['absences']}
    - Past failures: {key_features['failures']}
    - School support: {key_features['schoolsup']}
    - Grades: G1={key_features['G1']}, G2={key_features['G2']}, G3={key_features['G3']}

    Based on this information, provide a short, tailored mentoring message in a {tone} tone. The message should be helpful and not judgmental.

    The advice should:
    - Briefly acknowledge their current status.
    - Provide a concrete, easy-to-follow recommendation.
    - Offer encouragement and a positive outlook.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not generate mentoring advice due to an API error: {e}"

def display_results(risk_level, advice):
    """Displays the predicted risk and LLM advice to the user."""
    
    if risk_level == 'High':
        st.error(f"⚠️ Predicted Risk: {risk_level}")
    elif risk_level == 'Medium':
        st.warning(f"🟡 Predicted Risk: {risk_level}")
    else:
        st.success(f"🟢 Predicted Risk: {risk_level}")
        
    st.markdown("---")
    st.subheader("Personalized Mentoring Advice")
    st.info(advice)

# --------------------
# 2. MODEL LOADING AND UI
# --------------------

try:
    model_pipeline = joblib.load('early_warning_model_pipeline.joblib')
except FileNotFoundError:
    st.error("Error: The model file 'early_warning_model_pipeline.joblib' was not found.")
    st.stop()

st.set_page_config(
    page_title="AI Student Mentor",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 AI-Powered Student Mentor")
st.markdown("Enter a student's data to get a personalized risk assessment and mentoring advice.")

# Create the input form
col1, col2, col3 = st.columns(3)

with col1:
    school = st.selectbox("School", ["GP", "MS"])
    age = st.slider("Age", 15, 22, 17)
    sex = st.selectbox("Sex", ["M", "F"])
    address = st.selectbox("Address Type", ["U", "R"])
    famsize = st.selectbox("Family Size", ["GT3", "LE3"])
    Pstatus = st.selectbox("Parent's Status", ["T", "A"])
    Medu = st.slider("Mother's Education (0-4)", 0, 4)
    Fedu = st.slider("Father's Education (0-4)", 0, 4)
    traveltime = st.slider("Travel Time (1-4)", 1, 4)
    studytime = st.slider("Study Time (1-4)", 1, 4)
    famrel = st.slider("Family Relationship (1-5)", 1, 5)

with col2:
    freetime = st.slider("Free Time (1-5)", 1, 5)
    goout = st.slider("Going Out (1-5)", 1, 5)
    Dalc = st.slider("Workday Alcohol (1-5)", 1, 5)
    Walc = st.slider("Weekend Alcohol (1-5)", 1, 5)
    health = st.slider("Health Status (1-5)", 1, 5)
    absences = st.slider("Absences", 0, 93, 5)
    G1 = st.slider("First Period Grade (0-20)", 0, 20, 10)
    G2 = st.slider("Second Period Grade (0-20)", 0, 20, 10)
    G3 = st.slider("Final Grade (0-20)", 0, 20, 10)
    failures = st.slider("Past Failures", 0, 4, 0)
    guardian = st.selectbox("Guardian", ["mother", "father", "other"])
    schoolsup = st.selectbox("School Support", ["yes", "no"])
    famsup = st.selectbox("Family Support", ["yes", "no"])

with col3:
    paid = st.selectbox("Paid Classes", ["yes", "no"])
    activities = st.selectbox("Extracurricular Activities", ["yes", "no"])
    nursery = st.selectbox("Attended Nursery", ["yes", "no"])
    higher = st.selectbox("Wants to Take Higher Ed", ["yes", "no"])
    internet = st.selectbox("Internet Access", ["yes", "no"])
    romantic = st.selectbox("In a Romantic Relationship", ["yes", "no"])
    Mjob = st.selectbox("Mother's Job", ['at_home', 'health', 'other', 'services', 'teacher'])
    Fjob = st.selectbox("Father's Job", ['at_home', 'health', 'other', 'services', 'teacher'])
    reason = st.selectbox("Reason for Choosing School", ['course', 'other', 'home', 'reputation'])


# Button to trigger the analysis
if st.button("Generate Mentoring Advice"):
    with st.spinner("Analyzing student profile..."):
        input_df = pd.DataFrame([{
            'school': school, 'age': age, 'sex': sex, 'address': address, 'famsize': famsize,
            'Pstatus': Pstatus, 'Medu': Medu, 'Fedu': Fedu, 'Mjob': Mjob, 'Fjob': Fjob,
            'reason': reason, 'guardian': guardian, 'traveltime': traveltime, 'studytime': studytime,
            'failures': failures, 'schoolsup': schoolsup, 'famsup': famsup, 'paid': paid,
            'activities': activities, 'nursery': nursery, 'higher': higher, 'internet': internet,
            'romantic': romantic, 'famrel': famrel, 'freetime': freetime, 'goout': goout,
            'Dalc': Dalc, 'Walc': Walc, 'health': health, 'absences': absences,
            'G1': G1, 'G2': G2, 'G3': G3
        }])

        try:
            prediction_proba = model_pipeline.predict_proba(input_df)[0]
            risk_labels = model_pipeline.classes_
            predicted_risk = risk_labels[prediction_proba.argmax()]
            
            key_features = {
                'absences': absences,
                'G1': G1,
                'G2': G2,
                'G3': G3,
                'failures': failures,
                'schoolsup': schoolsup
            }

            mentoring_advice = generate_llm_advice(predicted_risk, key_features)
            display_results(predicted_risk, mentoring_advice)

        except Exception as e:
            st.error(f"An error occurred during prediction: {e}")