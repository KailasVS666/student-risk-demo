import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
from collections import Counter
from imblearn.over_sampling import SMOTE
import warnings
import xgboost as xgb

# Suppress the UserWarning from scikit-learn regarding feature names
warnings.filterwarnings("ignore", category=UserWarning)

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
# 2. FEATURE ENGINEERING & PREPROCESSING
# --------------------
# Create new features to potentially improve model performance

# Feature 1: The change in performance from G1 to G2
combined_df['grade_change'] = combined_df['G2'] - combined_df['G1']

# Feature 2: The average grade from G1 and G2
combined_df['average_grade'] = (combined_df['G1'] + combined_df['G2']) / 2


# Identify features and target.
# We must drop 'G3' as it's the basis for the target variable 'risk_level'.
# Keeping it would be leaking information to the model.
features = combined_df.drop(['risk_level', 'G3'], axis=1)
target = combined_df['risk_level']


# Split data into training and testing sets for evaluation
X_train, X_test, y_train, y_test = train_test_split(
    features, target, test_size=0.2, random_state=42, stratify=target
)

# --- START OF FIX: Encode string labels to numerical ---
le = LabelEncoder()
y_train_encoded = le.fit_transform(y_train)
y_test_encoded = le.transform(y_test)
# --- END OF FIX ---


# Identify numeric and categorical columns for preprocessing
numeric_features = X_train.select_dtypes(include=['int64', 'float64']).columns
categorical_features = X_train.select_dtypes(include=['object']).columns

# Create a preprocessor to handle different feature types
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# Apply the preprocessor to the training and test data
X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

# Check and address class imbalance using SMOTE
print("\nClass distribution before SMOTE:", Counter(y_train_encoded))
oversampler = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = oversampler.fit_resample(X_train_processed, y_train_encoded)
print("Class distribution after SMOTE:", Counter(y_train_resampled))


# --------------------
# 3. MODEL TRAINING & HYPERPARAMETER TUNING
# --------------------

# Create the full pipeline with only the model (preprocessing is done)
model_pipeline = Pipeline(steps=[('classifier', xgb.XGBClassifier(random_state=42, eval_metric='mlogloss'))])

# Define the hyperparameter grid to search
param_grid = {
    'classifier__n_estimators': [100, 200, 300],
    'classifier__max_depth': [3, 6, 9],
    'classifier__learning_rate': [0.05, 0.1, 0.2]
}

# Create the GridSearchCV object
grid_search = GridSearchCV(model_pipeline, param_grid, cv=5, scoring='accuracy', n_jobs=-1)

print("\nStarting Grid Search for optimal hyperparameters...")
# Fit the grid search to the resampled training data
grid_search.fit(X_train_resampled, y_train_resampled)

print("\nBest parameters found: ", grid_search.best_params_)
print("Best cross-validation accuracy: {:.4f}".format(grid_search.best_score_))

# Evaluate the best model on the unseen test data
y_pred_tuned_encoded = grid_search.best_estimator_.predict(X_test_processed)
# --- START OF FIX: Decode predictions back to string labels for evaluation ---
y_pred_tuned = le.inverse_transform(y_pred_tuned_encoded)
# --- END OF FIX ---
accuracy_tuned = accuracy_score(y_test, y_pred_tuned)
precision_tuned = precision_score(y_test, y_pred_tuned, average='weighted', zero_division=0)
recall_tuned = recall_score(y_test, y_pred_tuned, average='weighted', zero_division=0)

print("\n--- Tuned Model Performance on Test Data ---")
print(f"Accuracy: {accuracy_tuned:.4f}")
print(f"Precision: {precision_tuned:.4f}")
print(f"Recall: {recall_tuned:.4f}")


# --------------------
# 4. SAVE PRODUCTION-READY MODELS
# --------------------
# Retrain the best model on the full dataset for final production use
print("\nRetraining the best model on full dataset for production...")

# Combine preprocessing and the best estimator into a single pipeline
# --- START OF FIX: The full pipeline needs to handle the target variable encoding as well ---
# Note: For production, it's often better to save the LabelEncoder as well, but for this fix,
# we'll train the final model on the already-encoded full dataset.
# So, we'll encode the full target variable first.
target_encoded_full = le.transform(target)
# --- END OF FIX ---

final_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                 ('classifier', grid_search.best_estimator_.named_steps['classifier'])])

final_pipeline.fit(features, target_encoded_full)

# Save the full pipeline for making predictions
joblib.dump(final_pipeline, 'early_warning_model_pipeline_tuned.joblib')
print("Full model pipeline saved to 'early_warning_model_pipeline_tuned.joblib'.")

# Extract and save the core classifier for SHAP explanations
trained_classifier = final_pipeline.named_steps['classifier']
joblib.dump(trained_classifier, 'student_risk_classifier_tuned.joblib')
print("Core classifier saved to 'student_risk_classifier_tuned.joblib' for SHAP explanations.")

# (At the end of the file, after the other joblib.dump calls)
joblib.dump(le, 'label_encoder.joblib')
print("Label encoder saved to 'label_encoder.joblib'.")