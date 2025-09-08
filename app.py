import streamlit as st
import pandas as pd
import joblib
import google.generativeai as genai

# --------------------
# 1. SETUP AND CONFIGURATION (Runs only once)
# --------------------

st.set_page_config(
    page_title="AI Student Mentor",
    page_icon="🎓",
    layout="centered"
)

# --- API and Model Configuration ---
# This is now at the top, so it runs only once and is more efficient.
try:
    # Use Streamlit's secrets management for the API key
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # Initialize the model once for the entire session
    llm_model = genai.GenerativeModel('gemini-1.5-flash')
except KeyError:
    st.error("Error: GOOGLE_API_KEY not found. Please add it to your Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"An error occurred during API configuration: {e}")
    st.stop()

# --- ML Model Loading ---
try:
    model_pipeline = joblib.load('early_warning_model_pipeline.joblib')
except FileNotFoundError:
    st.error("Error: The model file 'early_warning_model_pipeline.joblib' was not found.")
    st.stop()

# --------------------
# 2. HELPER FUNCTIONS
# --------------------

def generate_llm_advice(risk_level, key_features):
    """
    Generates a personalized and structured mentoring message using the Gemini model.
    This function now uses a much more detailed and structured prompt.
    """
    # Mappings for providing more descriptive context to the AI
    school_support_map = {'yes': 'is receiving extra educational support', 'no': 'is not currently receiving extra educational support'}
    higher_edu_map = {'yes': 'Aspires to pursue higher education', 'no': 'Does not plan to pursue higher education'}

    # The new, advanced prompt with a clear role, context, and a required output format
    prompt = f"""
    **Role and Goal:** You are an expert, empathetic, and highly motivational student mentor. Your goal is to provide supportive, personalized, and actionable advice to a high school student based on their academic profile. Your tone should be encouraging and constructive, never judgmental.

    **Student Profile Analysis:**
    - **Predicted Academic Risk Level:** {risk_level}
    - **Academic Performance:**
        - First Period Grade (G1): {key_features['G1']} out of 20
        - Second Period Grade (G2): {key_features['G2']} out of 20
        - Final Grade (G3): {key_features['G3']} out of 20
    - **Engagement and History:**
        - Number of School Absences: {key_features['absences']} days
        - Past Class Failures: {key_features['failures']}
    - **Support Systems:**
        - School Support Status: The student {school_support_map.get(key_features.get('schoolsup', 'no'), 'not specified')}.
    - **Future Plans:** {higher_edu_map.get(key_features.get('higher', 'no'), 'not specified')}. This is a core motivational factor.


    **Your Task:**
    Based on the profile above, generate personalized mentoring advice. Structure your response in Markdown using the following strict format:

    ### 1. Overall Assessment
    Begin with a brief, encouraging summary of the student's situation. Acknowledge their strengths and challenges based on the data.

    ### 2. Key Areas for Focus
    Identify the 2 most critical issues from the profile (e.g., trend in grades, high absences). Explain *why* these are important in a supportive manner.

    ### 3. Actionable Steps & Strategies
    Provide a bulleted list of specific, practical steps the student can take. For example, "speak with a school counselor to discuss any barriers to attendance."

    ### 4. Recommended Resources
    Suggest 1-2 relevant online resources (like Khan Academy, specific YouTube channels on study skills, etc.).
    """

    try:
        response = llm_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not generate mentoring advice due to an API error: {e}"

def display_results(risk_level, advice):
    """
    Displays the predicted risk and LLM advice.
    This now uses st.markdown for advice to render formatting correctly.
    """
    color = "green"
    if risk_level == 'High':
        color = "red"
    elif risk_level == 'Medium':
        color = "orange"

    st.header(f"Assessment Complete", divider=color)
    st.subheader(f"Predicted Risk: :{color}[{risk_level}]")
    
    st.subheader("Personalized Mentoring Advice")
    with st.container(border=True):
        st.markdown(advice)

# --------------------
# 3. USER INTERFACE
# --------------------

st.title("🎓 AI-Powered Student Mentor")
st.markdown("Enter a student's data to get a personalized risk assessment and mentoring advice.")

# Create the input form
col1, col2, col3 = st.columns(3)

with col1:
    school = st.selectbox("School", ["GP", "MS"])
    sex = st.selectbox("Sex", ["M", "F"])
    age = st.slider("Age", 15, 22, 17)
    address = st.selectbox("Address Type", ["U", "R"])
    famsize = st.selectbox("Family Size", ["GT3", "LE3"])
    Pstatus = st.selectbox("Parent's Status", ["T", "A"])
    Medu = st.slider("Mother's Education (0-4)", 0, 4)
    Fedu = st.slider("Father's Education (0-4)", 0, 4)
    traveltime = st.slider("Travel Time (1-4)", 1, 4)
    studytime = st.slider("Study Time (1-4)", 1, 4)
    failures = st.slider("Past Failures", 0, 4, 0)

with col2:
    schoolsup = st.selectbox("School Support", ["yes", "no"])
    famsup = st.selectbox("Family Support", ["yes", "no"])
    paid = st.selectbox("Paid Classes", ["yes", "no"])
    activities = st.selectbox("Extracurricular Activities", ["yes", "no"])
    nursery = st.selectbox("Attended Nursery", ["yes", "no"])
    higher = st.selectbox("Wants to Take Higher Ed", ["yes", "no"])
    internet = st.selectbox("Internet Access", ["yes", "no"])
    romantic = st.selectbox("In a Romantic Relationship", ["yes", "no"])
    famrel = st.slider("Family Relationship (1-5)", 1, 5)
    freetime = st.slider("Free Time (1-5)", 1, 5)
    goout = st.slider("Going Out (1-5)", 1, 5)

with col3:
    Dalc = st.slider("Workday Alcohol (1-5)", 1, 5)
    Walc = st.slider("Weekend Alcohol (1-5)", 1, 5)
    health = st.slider("Health Status (1-5)", 1, 5)
    absences = st.slider("Absences", 0, 93, 5)
    G1 = st.slider("First Period Grade (0-20)", 0, 20, 10)
    G2 = st.slider("Second Period Grade (0-20)", 0, 20, 10)
    G3 = st.slider("Final Grade (0-20)", 0, 20, 10)
    Mjob = st.selectbox("Mother's Job", ['at_home', 'health', 'other', 'services', 'teacher'])
    Fjob = st.selectbox("Father's Job", ['at_home', 'health', 'other', 'services', 'teacher'])
    reason = st.selectbox("Reason for Choosing School", ['course', 'other', 'home', 'reputation'])
    guardian = st.selectbox("Guardian", ["mother", "father", "other"])


# Button to trigger the analysis
if st.button("Generate Mentoring Advice", type="primary"):
    with st.spinner("Analyzing student profile..."):
        input_data = {
            'school': school, 'sex': sex, 'age': age, 'address': address, 'famsize': famsize,
            'Pstatus': Pstatus, 'Medu': Medu, 'Fedu': Fedu, 'Mjob': Mjob, 'Fjob': Fjob,
            'reason': reason, 'guardian': guardian, 'traveltime': traveltime, 'studytime': studytime,
            'failures': failures, 'schoolsup': schoolsup, 'famsup': famsup, 'paid': paid,
            'activities': activities, 'nursery': nursery, 'higher': higher, 'internet': internet,
            'romantic': romantic, 'famrel': famrel, 'freetime': freetime, 'goout': goout,
            'Dalc': Dalc, 'Walc': Walc, 'health': health, 'absences': absences,
            'G1': G1, 'G2': G2, 'G3': G3
        }
        input_df = pd.DataFrame([input_data])

        try:
            prediction_proba = model_pipeline.predict_proba(input_df)[0]
            risk_labels = model_pipeline.classes_
            predicted_risk = risk_labels[prediction_proba.argmax()]
            
            # The key_features dictionary now includes the 'higher' aspiration
            key_features_for_llm = {**input_data}

            mentoring_advice = generate_llm_advice(predicted_risk, key_features_for_llm)
            display_results(predicted_risk, mentoring_advice)

        except Exception as e:
            st.error(f"An error occurred during prediction: {e}")
