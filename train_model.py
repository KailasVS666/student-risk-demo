import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
import lightgbm as lgb
import joblib

# --- 1. Data Loading and Feature Engineering ---

# Load the dataset
try:
    df = pd.read_csv('student-por.csv', sep=';')
except FileNotFoundError:
    print("Error: student-por.csv not found. Make sure the dataset is in the root directory.")
    exit()

# Create engineered features, similar to the web app
df['grade_change'] = df['G2'] - df['G1']
df['average_grade'] = (df['G1'] + df['G2']) / 2

# --- 2. Target Variable Definition ---

# Define the target variable 'risk_level' based on the final grade (G3)
# This is an example logic; you can adjust the thresholds as needed.
bins = [-1, 9, 13, 20]
labels = ['High', 'Medium', 'Low']
df['risk_level'] = pd.cut(df['G3'], bins=bins, labels=labels)

# Drop rows where risk level is not defined (if any)
df.dropna(subset=['risk_level'], inplace=True)

# --- 3. Preprocessing and Model Pipeline ---

# Separate features (X) and target (y)
X = df.drop(['risk_level', 'G3'], axis=1)
y = df['risk_level']

# Encode the target variable
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Identify categorical and numerical features
categorical_features = X.select_dtypes(include=['object']).columns
numerical_features = X.select_dtypes(include=np.number).columns

# Create a preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# Create the full model pipeline with the classifier
model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', lgb.LGBMClassifier(random_state=42))
])

# --- 4. Model Training and Evaluation ---

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

# Train the model
print("Training the student risk classification model...")
model_pipeline.fit(X_train, y_train)
print("Training complete.")

# Evaluate the model
print("\n--- Model Evaluation ---")
y_pred = model_pipeline.predict(X_test)
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# --- 5. Save the Model and Encoder ---

# Save the entire pipeline
pipeline_filename = 'early_warning_model_pipeline_tuned.joblib'
joblib.dump(model_pipeline, pipeline_filename)
print(f"Model pipeline saved to: {pipeline_filename}")

# Save the label encoder
label_encoder_filename = 'label_encoder.joblib'
joblib.dump(label_encoder, label_encoder_filename)
print(f"Label encoder saved to: {label_encoder_filename}")

# Save the core model for SHAP explanations (optional but good practice)
core_model = model_pipeline.named_steps['classifier']
core_model_filename = 'student_risk_classifier_tuned.joblib'
joblib.dump(core_model, core_model_filename)
print(f"Core classification model saved to: {core_model_filename}")