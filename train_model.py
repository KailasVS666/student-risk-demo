import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load only the math student data
mat_df = pd.read_csv('student-mat.csv', sep=';')

# Define the target variable: risk_level based on the final grade (G3)
def get_risk_level(grade):
    if grade >= 15:
        return 'Low'
    elif grade >= 10:
        return 'Medium'
    else:
        return 'High'

mat_df['risk_level'] = mat_df['G3'].apply(get_risk_level)

# Identify features and target
features = mat_df.drop('risk_level', axis=1)
target = mat_df['risk_level']

# Identify numeric and categorical columns for preprocessing
numeric_features = features.select_dtypes(include=['int64', 'float64']).columns
categorical_features = features.select_dtypes(include=['object']).columns

# Create a preprocessor to handle different feature types
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# Create the full pipeline with preprocessing and the model
model_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                  ('classifier', RandomForestClassifier(random_state=42))])

# Train the model on the full dataset
model_pipeline.fit(features, target)

# --- Save the full pipeline for making predictions ---
joblib.dump(model_pipeline, 'early_warning_model_pipeline.joblib')
print("Full model pipeline saved to 'early_warning_model_pipeline.joblib'.")


# --- NEW: Extract and save the core classifier for SHAP explanations ---
# 1. Extract the trained classifier from the final step of the pipeline
trained_classifier = model_pipeline.named_steps['classifier']

# 2. Save this extracted model to a new file
joblib.dump(trained_classifier, 'student_risk_classifier.joblib')
print("Core classifier saved to 'student_risk_classifier.joblib' for SHAP explanations.")
