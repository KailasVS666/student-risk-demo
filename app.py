import streamlit as st
import pandas as pd
import joblib
import google.generativeai as genai
import shap
import matplotlib.pyplot as plt

# --------------------
# 1. SETUP AND CONFIGURATION
# --------------------

st.set_page_config(
    page_title="AI Student Mentor",
    page_icon="🎓",
    layout="wide"
)

# --- API and Model Configuration ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    llm_model = genai.GenerativeModel('gemini-1.5-flash')
except KeyError:
    st.error(
        "Error: GOOGLE_API_KEY not found. "
        "Please add it to your Streamlit secrets."
    )
    st.stop()
except Exception as e:
    st.error(f"An error occurred during API configuration: {e}")
    st.stop()

# --- ML Model Loading ---
try:
    model_pipeline = joblib.load('early_warning_model_pipeline.joblib')
    classifier_model = joblib.load('student_risk_classifier.joblib')
except FileNotFoundError:
    st.error(
        "Error: A required model file was not found. "
        "Please run train_model.py."
    )
    st.stop()

# --- Data Loading with Caching ---
@st.cache_data
def load_data(filepath):
    """Loads the student dataset for calculating averages."""
    try:
        return pd.read_csv(filepath, sep=';')
    except FileNotFoundError:
        st.error(f"Error: The data file '{filepath}' was not found.")
        return None

df = load_data('student-mat.csv')
if df is not None:
    def get_risk_level(grade):
        if grade >= 15: return 'Low'
        if grade >= 10: return 'Medium'
        return 'High'
    df['risk_level'] = df['G3'].apply(get_risk_level)
else:
    st.stop()

# --- SHAP Explainer Setup ---
try:
    preprocessor = model_pipeline.named_steps['preprocessor']
    # Create a background dataset using the training data features
    background_data = preprocessor.transform(df.drop('risk_level', axis=1))
    # Use the modern, general shap.Explainer.
    explainer = shap.Explainer(classifier_model, background_data)
except Exception as e:
    st.error(f"Failed to create SHAP explainer: {e}")
    st.stop()

# --------------------
# 2. HELPER FUNCTIONS
# --------------------

def generate_llm_advice(risk_level, student_features):
    """Generates a structured mentoring message using the Gemini model."""
    school_support_map = {
        'yes': 'is receiving extra educational support',
        'no': 'is not currently receiving extra educational support'
    }
    higher_edu_map = {
        'yes': 'Aspires to pursue higher education',
        'no': 'Does not plan to pursue higher education'
    }
    prompt = f"""
    **Role and Goal:** You are an expert, empathetic, and highly motivational student mentor. Your goal is to provide supportive, personalized, and actionable advice to a high school student based on their academic profile. Your tone should be encouraging and constructive, never judgmental.

    **Student Profile Analysis:**
    - **Predicted Academic Risk Level:** {risk_level}
    - **Academic Performance:**
        - First Period Grade (G1): {student_features['G1']} out of 20
        - Second Period Grade (G2): {student_features['G2']} out of 20
        - Final Grade (G3): {student_features['G3']} out of 20
    - **Engagement and History:**
        - Number of School Absences: {student_features['absences']} days
        - Past Class Failures: {student_features['failures']}
    - **Support Systems:**
        - School Support Status: The student {school_support_map.get(student_features.get('schoolsup', 'no'), 'not specified')}.
    - **Future Plans:** {higher_edu_map.get(student_features.get('higher', 'no'), 'not specified')}. This is a core motivational factor.

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


# --- REPLACEMENT for the display_shap_explanation function ---

def display_shap_explanation(input_df):
    """Displays the SHAP explanation chart for the prediction."""
    st.subheader("What Influenced This Prediction?")
    with st.spinner("Generating explanation chart..."):
        try:
            processed_input = model_pipeline.named_steps['preprocessor'].transform(input_df)
            
            # The explainer returns a multi-output object
            shap_values = explainer(processed_input)
            
            class_names = model_pipeline.classes_
            high_risk_idx = list(class_names).index('High')

            with st.container(border=True):
                # --- THIS TEXT IS NOW MUCH CLEARER ---
                st.write("""
                This chart explains the model's score for the **'High' risk category**.
                - **<span style='color:red;'>Red bars</span>** represent factors that pushed the probability of being 'High Risk' **higher**.
                - **<span style='color:blue;'>Blue bars</span>** represent factors that pushed the probability of being 'High Risk' **lower**.
                
                Even if the final prediction is 'Medium' or 'Low', this chart shows you why the student was (or wasn't) considered 'High' risk.
                """, unsafe_allow_html=True)

                # The plotting code remains the same as it is correct
                shap_values.display_features = input_df.iloc[0]
                shap.force_plot(
                    shap_values.base_values[0, high_risk_idx],
                    shap_values.values[0, :, high_risk_idx],
                    matplotlib=True,
                    show=False
                )
                fig = plt.gcf()
                fig.set_layout_engine('tight')
                st.pyplot(fig, use_container_width=True)
                plt.clf()

        except Exception as e:
            st.error(f"Could not generate the explanation chart. Error: {e}")
def display_results(risk, advice, student_data, full_df, df_for_shap):
    """Displays all results: prediction, explanation, snapshot, and advice."""
    color_map = {'High': 'red', 'Medium': 'orange', 'Low': 'green'}
    color = color_map.get(risk, "green")

    st.header("Assessment Complete", divider=color)
    st.subheader(f"Predicted Risk: :{color}[{risk}]")

    display_shap_explanation(df_for_shap)

    st.subheader("Student Snapshot vs. Class Average")
    avg_g3 = full_df['G3'].mean()
    avg_absences = full_df['absences'].mean()
    avg_studytime = full_df['studytime'].mean()

    cols = st.columns(3)
    with cols[0]:
        st.metric(
            "Final Grade (G3)",
            f"{student_data['G3']}",
            f"{student_data['G3'] - avg_g3:.1f} (vs avg)"
        )
    with cols[1]:
        st.metric(
            "Absences",
            f"{student_data['absences']}",
            f"{student_data['absences'] - avg_absences:.1f} (vs avg)",
            delta_color="inverse"
        )
    with cols[2]:
        time_map = {1: "< 2 hrs", 2: "2-5 hrs", 3: "5-10 hrs", 4: "> 10 hrs"}
        st.metric(
            "Weekly Study Time",
            time_map.get(student_data['studytime']),
            f"{student_data['studytime'] - avg_studytime:.1f} (vs avg index)"
        )

    st.subheader("Personalized Mentoring Advice")
    with st.container(border=True):
        st.markdown(advice)


# --------------------
# 3. USER INTERFACE
# --------------------
st.title("🎓 AI-Powered Student Mentor")
st.markdown(
    "Enter a student's data for a risk assessment, a breakdown of "
    "influencing factors, and personalized mentoring advice."
)

ui_cols = st.columns(3)
with ui_cols[0]:
    school = st.selectbox("School", ["GP", "MS"])
    sex = st.selectbox("Sex", ["M", "F"])
    age = st.slider("Age", 15, 22, 17)
    address = st.selectbox("Address Type", ["U", "R"])
    famsize = st.selectbox(
        "Family Size", ["GT3", "LE3"],
        format_func=lambda x: "Greater than 3" if x == "GT3" else "3 or less"
    )
    Pstatus = st.selectbox("Parent's Status", ["T", "A"])
    Medu = st.slider("Mother's Education (0-4)", 0, 4)
    Fedu = st.slider("Father's Education (0-4)", 0, 4)
    traveltime = st.slider("Travel Time (1-4)", 1, 4)
    studytime = st.slider("Study Time (1-4)", 1, 4)
    failures = st.slider("Past Failures", 0, 4, 0)

with ui_cols[1]:
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

with ui_cols[2]:
    Dalc = st.slider("Workday Alcohol (1-5)", 1, 5)
    Walc = st.slider("Weekend Alcohol (1-5)", 1, 5)
    health = st.slider("Health Status (1-5)", 1, 5)
    absences = st.slider("Absences", 0, 93, 5)
    G1 = st.slider("First Period Grade (0-20)", 0, 20, 10)
    G2 = st.slider("Second Period Grade (0-20)", 0, 20, 10)
    G3 = st.slider("Final Grade (0-20)", 0, 20, 10)
    Mjob = st.selectbox(
        "Mother's Job",
        ['at_home', 'health', 'other', 'services', 'teacher']
    )
    Fjob = st.selectbox(
        "Father's Job",
        ['at_home', 'health', 'other', 'services', 'teacher']
    )
    reason = st.selectbox(
        "Reason for Choosing School",
        ['course', 'other', 'home', 'reputation']
    )
    guardian = st.selectbox("Guardian", ["mother", "father", "other"])

if st.button("Generate Mentoring Advice", type="primary"):
    with st.spinner("Analyzing student profile..."):
        input_data = {
            'school': school, 'sex': sex, 'age': age, 'address': address,
            'famsize': famsize, 'Pstatus': Pstatus, 'Medu': Medu, 'Fedu': Fedu,
            'Mjob': Mjob, 'Fjob': Fjob, 'reason': reason,
            'guardian': guardian, 'traveltime': traveltime,
            'studytime': studytime, 'failures': failures,
            'schoolsup': schoolsup, 'famsup': famsup, 'paid': paid,
            'activities': activities, 'nursery': nursery, 'higher': higher,
            'internet': internet, 'romantic': romantic, 'famrel': famrel,
            'freetime': freetime, 'goout': goout, 'Dalc': Dalc,
            'Walc': Walc, 'health': health, 'absences': absences, 'G1': G1,
            'G2': G2, 'G3': G3
        }
        input_df = pd.DataFrame([input_data])

        try:
            pred_proba = model_pipeline.predict_proba(input_df)[0]
            pred_risk = model_pipeline.classes_[pred_proba.argmax()]
            advice = generate_llm_advice(pred_risk, input_data)
            display_results(pred_risk, advice, input_data, df, input_df)
        except Exception as e:
            st.error(f"An error occurred during prediction: {e}")

