import streamlit as st
import pandas as pd
import joblib
import google.generativeai as genai
import shap
import matplotlib.pyplot as plt
import json
import os

# --------------------
# 1. SETUP AND CONFIGURATION
# --------------------

st.set_page_config(
    page_title="AI Student Mentor",
    page_icon="雌",
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
    """Loads a single student dataset."""
    try:
        return pd.read_csv(filepath, sep=';')
    except FileNotFoundError:
        st.error(f"Error: The data file '{filepath}' was not found.")
        return None

# Load both math and portuguese student data
mat_df = load_data('student-mat.csv')
por_df = load_data('student-por.csv')

# Combine the two dataframes if both are loaded successfully
if mat_df is not None and por_df is not None:
    df = pd.concat([mat_df, por_df], ignore_index=True)
    def get_risk_level(grade):
        if grade >= 15:
            return 'Low'
        if grade >= 10:
            return 'Medium'
        return 'High'
    df['risk_level'] = df['G3'].apply(get_risk_level)
else:
    st.stop()

# --- SHAP Explainer Setup ---
try:
    preprocessor = model_pipeline.named_steps['preprocessor']
    background_data = preprocessor.transform(df.drop('risk_level', axis=1))
    explainer = shap.Explainer(classifier_model, background_data)
except Exception as e:
    st.error(f"Failed to create SHAP explainer: {e}")
    st.stop()

# --------------------
# 2. HELPER FUNCTIONS
# --------------------
def save_student_profile(student_data, filename):
    """Saves a student profile to a JSON file."""
    if not os.path.exists("student_history"):
        os.makedirs("student_history")
    filepath = os.path.join("student_history", filename)
    with open(filepath, 'w') as f:
        json.dump(student_data, f, indent=4)

def load_student_profile(filename):
    """Loads a student profile from a JSON file."""
    filepath = os.path.join("student_history", filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def get_grade_trend(g1, g2, g3):
    """Determines the student's grade trend."""
    if g1 > g2 and g2 > g3:
        return "a consistent decline in grades"
    elif g1 < g2 and g2 < g3:
        return "a positive, improving trend"
    elif g1 == g2 and g2 == g3:
        return "a stable, consistent performance"
    elif g3 < g2 and g3 < g1:
        return "a recent significant drop in the final period"
    elif g3 > g2 and g3 > g1:
        return "a significant improvement in the final period"
    else:
        return "a mixed performance trend"

def generate_llm_advice(risk_level, student_features, grade_trend, top_shap_factors):
    """Generates a structured mentoring message using the Gemini model."""
    school_support_map = {
        'yes': 'is receiving extra educational support',
        'no': 'is not currently receiving extra educational support'
    }
    higher_edu_map = {
        'yes': 'Aspires to pursue higher education',
        'no': 'Does not plan to pursue higher education'
    }

    shap_factors_text = ""
    if top_shap_factors:
        shap_factors_text = (
            f"The model identified the following as the most influential factors "
            f"in this assessment: **{', '.join(top_shap_factors)}**."
        )

    prompt = f"""
    **Role and Goal:** You are an expert, empathetic, and highly motivational student mentor. Your goal is to provide supportive, personalized, and actionable advice to a high school student based on their academic profile. Your tone should be encouraging and constructive, never judgmental.

    **Student Profile Analysis:**
    - **Predicted Academic Risk Level:** {risk_level}
    - **Academic Performance:**
        - First Period Grade (G1): {student_features['G1']} out of 20
        - Second Period Grade (G2): {student_features['G2']} out of 20
        - Final Grade (G3): {student_features['G3']} out of 20
    - **Grade Trend:** The student has shown {grade_trend}.
    - **Engagement and History:**
        - Number of School Absences: {student_features['absences']} days
        - Past Class Failures: {student_features['failures']}
    - **Support Systems:**
        - School Support Status: The student {school_support_map.get(student_features.get('schoolsup', 'no'), 'not specified')}.
    - **Future Plans:** {higher_edu_map.get(student_features.get('higher', 'no'), 'not specified')}. This is a core motivational factor.

    **Model Insights:**
    {shap_factors_text}

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


def display_shap_explanation(input_df):
    """Displays the SHAP explanation chart with human-readable feature names."""
    st.subheader("What Influenced This Prediction?")
    with st.spinner("Generating explanation chart..."):
        try:
            processed_input = model_pipeline.named_steps['preprocessor'].transform(input_df)
            shap_values = explainer(processed_input)
            class_names = model_pipeline.classes_
            high_risk_idx = list(class_names).index('High')

            shap_values.display_features = input_df.iloc[0]

            with st.container(border=True):
                st.write("""
                This chart explains the model's score for the **'High' risk category**.
                - **<span style='color:red;'>Red bars</span>** pushed the probability of being 'High Risk' **higher**.
                - **<span style='color:blue;'>Blue bars</span>** pushed it **lower**.
                Even if the final prediction is 'Medium' or 'Low', this chart shows why the student was (or wasn't) considered 'High' risk.
                """, unsafe_allow_html=True)
                
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

            return shap_values.values[0, :, high_risk_idx]

        except Exception as e:
            st.error(f"Could not generate the explanation chart. Error: {e}")
            return None


def display_high_risk_actions():
    """Displays the intervention section for High Risk students."""
    st.subheader("Immediate Action Steps")
    with st.container(border=True):
        st.warning(
            "Based on the assessment, we strongly recommend taking immediate "
            "steps to connect with school support systems."
        )
        cols = st.columns(2)
        with cols[0]:
            st.link_button(
                "套 Schedule Meeting with Counselor",
                "mailto:counselor@yourschool.edu?subject=Request for Student Support Meeting"
            )
        with cols[1]:
            st.link_button(
                "答 Access Tutoring Resources", "https://www.khanacademy.org/"
            )


def display_low_risk_enrichment():
    """Displays the enrichment section for Low Risk students."""
    st.subheader("Enrichment Opportunities")
    with st.container(border=True):
        st.success(
            "Great work! Your profile shows strong academic standing. "
            "Consider these resources to challenge yourself further."
        )
        cols = st.columns(2)
        with cols[0]:
            st.link_button(
                "溌 Explore Advanced Science Projects",
                "https://www.sciencebuddies.org/"
            )
        with cols[1]:
            st.link_button(
                "醇 Prepare for Academic Competitions",
                "https://www.aqocl.com/"
            )


def display_full_analysis(student_data, full_df, df_for_shap, advice):
    """Displays the standard analysis view (Snapshot, SHAP, and AI Advice)."""
    display_shap_explanation(df_for_shap)

    st.subheader("Student Snapshot vs. Class Average")
    avg_g3 = full_df['G3'].mean()
    avg_absences = full_df['absences'].mean()
    avg_studytime = full_df['studytime'].mean()
    cols = st.columns(3)
    with cols[0]:
        st.metric("Final Grade (G3)", f"{student_data['G3']}", f"{student_data['G3'] - avg_g3:.1f} (vs avg)")
    with cols[1]:
        st.metric("Absences", f"{student_data['absences']}", f"{student_data['absences'] - avg_absences:.1f} (vs avg)", "inverse")
    with cols[2]:
        time_map = {1: "< 2 hrs", 2: "2-5 hrs", 3: "5-10 hrs", 4: "> 10 hrs"}
        st.metric("Weekly Study Time", time_map.get(student_data['studytime']), f"{student_data['studytime'] - avg_studytime:.1f} (vs avg index)")

    st.subheader("Personalized Mentoring Advice")
    with st.container(border=True):
        st.markdown(advice)


def display_results(risk, advice, student_data, full_df, df_for_shap):
    """Acts as a router to display different UI based on risk level."""
    color_map = {'High': 'red', 'Medium': 'orange', 'Low': 'green'}
    color = color_map.get(risk, "green")
    st.header("Assessment Complete", divider=color)
    st.subheader(f"Predicted Risk: :{color}[{risk}]")

    if risk == 'High':
        display_high_risk_actions()
        display_full_analysis(student_data, full_df, df_for_shap, advice)
    elif risk == 'Medium':
        display_full_analysis(student_data, full_df, df_for_shap, advice)
    else:  # Low Risk
        display_low_risk_enrichment()
        st.subheader("Personalized Mentoring Advice")
        with st.container(border=True):
            st.markdown(advice)


# --------------------
# 3. USER INTERFACE
# --------------------

view_mode = st.radio(
    "Select View Mode:",
    ["Individual Student Analysis", "Administrative Dashboard"],
    index=0,
    horizontal=True
)

if view_mode == "Individual Student Analysis":
    st.title("雌 AI-Powered Student Mentor")
    st.markdown("Enter student data for a risk assessment and risk-based action routing.")

    if 'loaded_profile' not in st.session_state:
        st.session_state.loaded_profile = {
            'school': 'GP', 'sex': 'M', 'age': 17, 'address': 'U',
            'famsize': 'GT3', 'Pstatus': 'T', 'Medu': 2, 'Fedu': 2,
            'Mjob': 'other', 'Fjob': 'other', 'reason': 'course', 'guardian': 'mother',
            'traveltime': 2, 'studytime': 2, 'failures': 0, 'schoolsup': 'no',
            'famsup': 'yes', 'paid': 'no', 'activities': 'no', 'nursery': 'yes',
            'higher': 'yes', 'internet': 'yes', 'romantic': 'no', 'famrel': 4,
            'freetime': 3, 'goout': 3, 'Dalc': 1, 'Walc': 1, 'health': 3,
            'absences': 5, 'G1': 10, 'G2': 10, 'G3': 10
        }
    if 'pred_risk' not in st.session_state:
        st.session_state.pred_risk = 'N/A'
    
    with st.sidebar:
        st.subheader("Student Profile Management")
        st.write("Save the current profile or load a past one.")
        
        # Save a profile
        save_filename = st.text_input("Filename to save as:", value="new_student.json")
        if st.button("Save Profile"):
            # Ensure the input data is current before saving
            current_data = {
                'school': school, 'sex': sex, 'age': age, 'address': address,
                'famsize': famsize, 'Pstatus': Pstatus, 'Medu': Medu, 'Fedu': Fedu,
                'Mjob': Mjob, 'Fjob': Fjob, 'reason': reason, 'guardian': guardian,
                'traveltime': traveltime, 'studytime': studytime,
                'failures': failures, 'schoolsup': schoolsup, 'famsup': famsup,
                'paid': paid, 'activities': activities, 'nursery': nursery,
                'higher': higher, 'internet': internet, 'romantic': romantic,
                'famrel': famrel, 'freetime': freetime, 'goout': goout,
                'Dalc': Dalc, 'Walc': Walc, 'health': health, 'absences': absences,
                'G1': G1, 'G2': G2, 'G3': G3
            }
            save_student_profile(current_data, save_filename)
            st.success(f"Profile saved as {save_filename}")
        
        # Load a profile
        try:
            history_files = [f for f in os.listdir("student_history") if f.endswith('.json')]
            load_filename = st.selectbox("Select Profile to Load", ["- Select -"] + history_files)
            if load_filename != "- Select -":
                loaded_data = load_student_profile(load_filename)
                if loaded_data:
                    st.session_state.loaded_profile = loaded_data
                    st.success(f"Profile '{load_filename}' loaded. Please press 'Generate Mentoring Advice' to analyze.")
        except FileNotFoundError:
            st.info("No student history profiles found. Save a profile to get started.")

    ui_cols = st.columns(3)
    with ui_cols[0]:
        school = st.selectbox("School", ["GP", "MS"], index=["GP", "MS"].index(st.session_state.loaded_profile['school']))
        sex = st.selectbox("Sex", ["M", "F"], index=["M", "F"].index(st.session_state.loaded_profile['sex']))
        age = st.slider("Age", 15, 22, st.session_state.loaded_profile['age'])
        address = st.selectbox("Address Type", ["U", "R"], index=["U", "R"].index(st.session_state.loaded_profile['address']))
        famsize = st.selectbox(
            "Family Size", ["GT3", "LE3"],
            format_func=lambda x: "Greater than 3" if x == "GT3" else "3 or less",
            index=["GT3", "LE3"].index(st.session_state.loaded_profile['famsize'])
        )
        Pstatus = st.selectbox("Parent's Status", ["T", "A"], index=["T", "A"].index(st.session_state.loaded_profile['Pstatus']))
        Medu = st.slider("Mother's Education (0-4)", 0, 4, st.session_state.loaded_profile['Medu'])
        Fedu = st.slider("Father's Education (0-4)", 0, 4, st.session_state.loaded_profile['Fedu'])
        traveltime = st.slider("Travel Time (1-4)", 1, 4, st.session_state.loaded_profile['traveltime'])
        studytime = st.slider("Study Time (1-4)", 1, 4, st.session_state.loaded_profile['studytime'])
        failures = st.slider("Past Failures", 0, 4, st.session_state.loaded_profile['failures'])

    with ui_cols[1]:
        schoolsup = st.selectbox("School Support", ["yes", "no"], index=["yes", "no"].index(st.session_state.loaded_profile['schoolsup']))
        famsup = st.selectbox("Family Support", ["yes", "no"], index=["yes", "no"].index(st.session_state.loaded_profile['famsup']))
        paid = st.selectbox("Paid Classes", ["yes", "no"], index=["yes", "no"].index(st.session_state.loaded_profile['paid']))
        activities = st.selectbox("Extracurricular Activities", ["yes", "no"], index=["yes", "no"].index(st.session_state.loaded_profile['activities']))
        nursery = st.selectbox("Attended Nursery", ["yes", "no"], index=["yes", "no"].index(st.session_state.loaded_profile['nursery']))
        higher = st.selectbox("Wants to Take Higher Ed", ["yes", "no"], index=["yes", "no"].index(st.session_state.loaded_profile['higher']))
        internet = st.selectbox("Internet Access", ["yes", "no"], index=["yes", "no"].index(st.session_state.loaded_profile['internet']))
        romantic = st.selectbox("In a Romantic Relationship", ["yes", "no"], index=["yes", "no"].index(st.session_state.loaded_profile['romantic']))
        famrel = st.slider("Family Relationship (1-5)", 1, 5, st.session_state.loaded_profile['famrel'])
        freetime = st.slider("Free Time (1-5)", 1, 5, st.session_state.loaded_profile['freetime'])
        goout = st.slider("Going Out (1-5)", 1, 5, st.session_state.loaded_profile['goout'])

    with ui_cols[2]:
        Dalc = st.slider("Workday Alcohol (1-5)", 1, 5, st.session_state.loaded_profile['Dalc'])
        Walc = st.slider("Weekend Alcohol (1-5)", 1, 5, st.session_state.loaded_profile['Walc'])
        health = st.slider("Health Status (1-5)", 1, 5, st.session_state.loaded_profile['health'])
        absences = st.slider("Absences", 0, 93, st.session_state.loaded_profile['absences'])
        G1 = st.slider("First Period Grade (0-20)", 0, 20, st.session_state.loaded_profile['G1'])
        G2 = st.slider("Second Period Grade (0-20)", 0, 20, st.session_state.loaded_profile['G2'])
        G3 = st.slider("Final Grade (0-20)", 0, 20, st.session_state.loaded_profile['G3'])
        Mjob = st.selectbox("Mother's Job", ['at_home', 'health', 'other', 'services', 'teacher'], index=['at_home', 'health', 'other', 'services', 'teacher'].index(st.session_state.loaded_profile['Mjob']))
        Fjob = st.selectbox("Father's Job", ['at_home', 'health', 'other', 'services', 'teacher'], index=['at_home', 'health', 'other', 'services', 'teacher'].index(st.session_state.loaded_profile['Fjob']))
        reason = st.selectbox("Reason", ['course', 'other', 'home', 'reputation'], index=['course', 'other', 'home', 'reputation'].index(st.session_state.loaded_profile['reason']))
        guardian = st.selectbox("Guardian", ["mother", "father", "other"], index=["mother", "father", "other"].index(st.session_state.loaded_profile['guardian']))

    # This dictionary is now created from the current UI state
    st.session_state.current_data = {
        'school': school, 'sex': sex, 'age': age, 'address': address,
        'famsize': famsize, 'Pstatus': Pstatus, 'Medu': Medu, 'Fedu': Fedu,
        'Mjob': Mjob, 'Fjob': Fjob, 'reason': reason, 'guardian': guardian,
        'traveltime': traveltime, 'studytime': studytime,
        'failures': failures, 'schoolsup': schoolsup, 'famsup': famsup,
        'paid': paid, 'activities': activities, 'nursery': nursery,
        'higher': higher, 'internet': internet, 'romantic': romantic,
        'famrel': famrel, 'freetime': freetime, 'goout': goout,
        'Dalc': Dalc, 'Walc': Walc, 'health': health, 'absences': absences,
        'G1': G1, 'G2': G2, 'G3': G3
    }

    if st.button("Generate Mentoring Advice", type="primary"):
        with st.spinner("Analyzing student profile..."):
            input_data = st.session_state.current_data
            input_df = pd.DataFrame([input_data])
            try:
                pred_proba = model_pipeline.predict_proba(input_df)[0]
                pred_risk = model_pipeline.classes_[pred_proba.argmax()]
                st.session_state.pred_risk = pred_risk

                processed_input = model_pipeline.named_steps['preprocessor'].transform(input_df)
                shap_values = explainer(processed_input)
                high_risk_idx = list(model_pipeline.classes_).index('High')
                
                abs_shap_values = abs(shap_values.values[0, :, high_risk_idx])
                
                top_features_indices = abs_shap_values.argsort()[-3:][::-1]
                top_shap_factors = [input_df.columns[i] for i in top_features_indices]

                grade_trend = get_grade_trend(input_data['G1'], input_data['G2'], input_data['G3'])

                advice = generate_llm_advice(pred_risk, input_data, grade_trend, top_shap_factors)

                display_results(pred_risk, advice, input_data, df, input_df)
            except Exception as e:
                st.error(f"An error occurred during prediction: {e}")

    st.header("What-If Analysis", divider=True)
    st.markdown("Select a feature to see how changing its value impacts the risk prediction.")
    with st.container(border=True):
        if st.session_state.pred_risk != 'N/A':
            what_if_cols = st.columns(3)
            with what_if_cols[0]:
                feature_to_change = st.selectbox(
                    "Select Feature to Change",
                    ['absences', 'G1', 'G2', 'G3', 'failures', 'studytime']
                )
            with what_if_cols[1]:
                original_value = st.session_state.current_data[feature_to_change]
                if feature_to_change in ['G1', 'G2', 'G3']:
                    new_value = st.slider(f"Change '{feature_to_change}' to:", 0, 20, original_value)
                elif feature_to_change == 'absences':
                    new_value = st.slider(f"Change '{feature_to_change}' to:", 0, 93, original_value)
                elif feature_to_change == 'failures':
                    new_value = st.slider(f"Change '{feature_to_change}' to:", 0, 4, original_value)
                else:
                    new_value = st.slider(f"Change '{feature_to_change}' to:", 1, 4, original_value)
            
            what_if_data = st.session_state.current_data.copy()
            what_if_data[feature_to_change] = new_value
            
            if st.button("Run What-If Prediction", key="what_if_button"):
                with st.spinner("Running what-if analysis..."):
                    what_if_df = pd.DataFrame([what_if_data])
                    what_if_pred_proba = model_pipeline.predict_proba(what_if_df)[0]
                    what_if_pred_risk = model_pipeline.classes_[what_if_pred_proba.argmax()]
                    
                    st.write(f"If the student's **{feature_to_change}** was **{new_value}**:")
                    st.metric(
                        "Predicted Risk Level",
                        what_if_pred_risk,
                        f"Original: {st.session_state.pred_risk}"
                    )
                    display_shap_explanation(what_if_df)
        else:
            st.info("Please set the student's profile by generating advice first.")

elif view_mode == "Administrative Dashboard":
    st.title("Administrative Dashboard")
    st.markdown("High-level overview of the student population.")
    
    num_students = len(df)
    avg_g3 = df['G3'].mean()
    high_risk_count = len(df[df['risk_level'] == 'High'])
    
    dashboard_cols = st.columns(3)
    with dashboard_cols[0]:
        st.metric("Total Students", num_students)
    with dashboard_cols[1]:
        st.metric("Average Final Grade", f"{avg_g3:.1f}")
    with dashboard_cols[2]:
        st.metric("High Risk Students", high_risk_count)
        
    st.header("Student Risk Distribution")
    risk_counts = df['risk_level'].value_counts().reindex(['High', 'Medium', 'Low'])
    st.bar_chart(risk_counts)
    
    st.header("Students by Risk Level")
    risk_level_filter = st.selectbox(
        "Filter by Risk Level", ["All", "High", "Medium", "Low"]
    )
    
    filtered_df = df if risk_level_filter == "All" else df[df['risk_level'] == risk_level_filter]
    st.dataframe(filtered_df[['school', 'sex', 'age', 'failures', 'absences', 'G3', 'risk_level']])