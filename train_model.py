import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib

# --------------------
# 1. DATA LOADING & PREPARATION
# --------------------

# Load both math and portuguese student data
mat_df = pd.read_csv('student-mat.csv', sep=';')
por_df = pd.read_csv('student-por.csv', sep=';')

# Concatenate the two dataframes
combined_df = pd.concat([mat_df, por_df], ignore_index=True)
print(f"Combined dataset size: {len(combined_df)} students.")

# Define the target variable: risk_level based on the final grade (G3)
def get_risk_level(grade):
    if grade >= 15:
        return 'Low'
    elif grade >= 10:
        return 'Medium'
    else:
        return 'High'

combined_df['risk_level'] = combined_df['G3'].apply(get_risk_level)

# --------------------
# *** IMPORTANT CHANGE HERE ***
# --------------------
# Identify features and target.
# We must drop 'G3' as it's the basis for the target variable 'risk_level'.
# Keeping it would be leaking information to the model.
features = combined_df.drop(['risk_level', 'G3'], axis=1)
target = combined_df['risk_level']


# Split data into training and testing sets for evaluation
X_train, X_test, y_train, y_test = train_test_split(
    features, target, test_size=0.2, random_state=42, stratify=target
)

# Identify numeric and categorical columns for preprocessing
numeric_features = X_train.select_dtypes(include=['int64', 'float64']).columns
categorical_features = X_train.select_dtypes(include=['object']).columns

# Create a preprocessor to handle different feature types
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# --------------------
# 2. MODEL TRAINING & EVALUATION
# --------------------

# Create the full pipeline with preprocessing and the model
model_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                  ('classifier', RandomForestClassifier(random_state=42))])

print("\nTraining model on combined dataset...")
# Train the model on the training data
model_pipeline.fit(X_train, y_train)
print("Model training complete.")

# Evaluate the model on the unseen test data
y_pred = model_pipeline.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)

print("\n--- Model Performance on Test Data ---")
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")

# --------------------
# 3. SAVE PRODUCTION-READY MODELS
# --------------------
# Retrain the model on the full dataset for final production use
print("\nRetraining model on full dataset for production...")
model_pipeline.fit(features, target)

# Save the full pipeline for making predictions
joblib.dump(model_pipeline, 'early_warning_model_pipeline.joblib')
print("Full model pipeline saved to 'early_warning_model_pipeline.joblib'.")

# Extract and save the core classifier for SHAP explanations
trained_classifier = model_pipeline.named_steps['classifier']
joblib.dump(trained_classifier, 'student_risk_classifier.joblib')
print("Core classifier saved to 'student_risk_classifier.joblib' for SHAP explanations.")