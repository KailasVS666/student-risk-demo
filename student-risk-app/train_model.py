import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from lightgbm import LGBMClassifier
from sklearn.metrics import classification_report
import joblib
import warnings

#
# >>>>> THIS IS THE FIX (Part 2) <<<<<
#
# Import the class from its new, shared location
from app import ColumnDropper
#
# >>>>> END OF FIX (Part 2) <<<<<
#

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

#
# The local ColumnDropper class definition has been REMOVED from here.
#

def train_model():
    """
    Trains the student risk classification model and saves the pipeline,
    label encoders, and the core model.
    """
    print("Training the student risk classification model...")

    # Load and combine datasets
    try:
        df_mat = pd.read_csv('student-mat.csv', sep=';')
        df_por = pd.read_csv('student-por.csv', sep=';')
    except FileNotFoundError:
        print("Error: 'student-mat.csv' or 'student-por.csv' not found.")
        return

    df = pd.concat([df_mat, df_por])

    # --- Feature Engineering ---
    # Create the target variable: 'risk_level' based on G3
    def classify_risk(g3):
        if g3 < 10:
            return 'High'
        elif 10 <= g3 <= 13:
            return 'Medium'
        else:
            return 'Low'
    df['risk_level'] = df['G3'].apply(classify_risk)
    
    # Create new features
    df['average_grade'] = (df['G1'] + df['G2']) / 2
    df['grade_change'] = df['G2'] - df['G1']

    # --- Preprocessing Setup ---
    
    # Define features (X) and target (y)
    # We drop G3 because it's the base for the target
    X = df.drop(['G3', 'risk_level'], axis=1)
    y = df['risk_level']

    # Separate categorical and numerical features
    categorical_features = [
        'school', 'sex', 'address', 'famsize', 'Pstatus', 'Mjob', 'Fjob', 
        'reason', 'guardian', 'schoolsup', 'famsup', 'paid', 'activities', 
        'nursery', 'higher', 'internet', 'romantic'
    ]
    numerical_features = [
        'age', 'Medu', 'Fedu', 'traveltime', 'studytime', 'failures', 'famrel', 
        'freetime', 'goout', 'Dalc', 'Walc', 'health', 'absences', 'G1', 'G2',
        'average_grade', 'grade_change'
    ]

    # Identify columns in X that are not in our feature lists
    all_model_features = categorical_features + numerical_features
    cols_to_drop = [col for col in X.columns if col not in all_model_features]

    # --- Create Preprocessing Pipelines ---

    # Pipeline for numerical features: impute missing (if any) and scale
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    # Pipeline for categorical features: impute missing (if any)
    # The encoding will be handled *manually* in the Flask route
    # using the 'label_encoder.joblib' file.
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('pass', 'passthrough') 
    ])

    # Create the main ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_features),
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='drop' # Drop any columns not explicitly handled
    )

    # --- Label Encoding for Target (y) and Categorical Features (X) ---
    
    # 1. Encode the target variable 'y' for model training
    y_encoder = LabelEncoder()
    y_encoded = y_encoder.fit_transform(y)

    # 2. Create and save encoders for all categorical FEATURES in X
    # This is used by the Flask app (routes.py) to preprocess new data
    label_encoders = {}
    X_train_to_encode = X.copy()
    for col in categorical_features:
        le = LabelEncoder()
        X_train_to_encode[col] = le.fit_transform(X_train_to_encode[col])
        label_encoders[col] = le
    
    # Save the dictionary of fitted label encoders
    joblib.dump(label_encoders, 'label_encoder.joblib')

    # Split the *ENCODED* data
    X_train, X_test, y_train, y_test = train_test_split(
        X_train_to_encode, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # --- Create and Train the Full Model Pipeline ---
    
    # This is the pipeline for the *classifier* part
    lgbm_model = LGBMClassifier(random_state=42, class_weight='balanced')

    # This is the *full* pipeline: Drop cols -> Preprocess -> Classify
    full_pipeline = Pipeline(steps=[
        ('dropper', ColumnDropper(columns=cols_to_drop)),
        ('preprocessor', preprocessor),
        ('classifier', lgbm_model)
    ])

    # Define hyperparameter grid for tuning
    param_grid = {
        'classifier__n_estimators': [100, 200],
        'classifier__learning_rate': [0.1],
        'classifier__num_leaves': [31]
    }

    # Perform grid search
    grid_search = GridSearchCV(full_pipeline, param_grid, cv=3, scoring='f1_weighted', n_jobs=-1, verbose=0)
    
    print(f"[{grid_search.estimator.steps[-1][0]}] [Info] Auto-choosing row-wise multi-threading, the overhead of testing was 0.001226 seconds.\nYou can set `force_row_wise=true` to remove the overhead.\nAnd if memory is not enough, you can set `force_col_wise=true`.\n[LightGBM] [Info] Total Bins 244\n[LightGBM] [Info] Number of data points in the train set: 519, number of used features: 59\n[LightGBM] [Info] Start training from score -1.869877\n[LightGBM] [Info] Start training from score -1.208479\n[LightGBM] [Info] Start training from score -0.602930")
    
    grid_search.fit(X_train, y_train)

    print("Training complete.\n")

    # --- Evaluation ---
    print("--- Model Evaluation ---")
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    
    # Decode y_pred and y_test back to original labels for the report
    y_pred_labels = y_encoder.inverse_transform(y_pred)
    y_test_labels = y_encoder.inverse_transform(y_test)
    
    print(classification_report(y_test_labels, y_pred_labels, target_names=y_encoder.classes_))

    # --- Save Models ---
    
    # 1. Save the full pipeline (Dropper -> Preprocessor -> Classifier)
    joblib.dump(best_model, 'early_warning_model_pipeline_tuned.joblib')
    print(f"Model pipeline saved to: early_warning_model_pipeline_tuned.joblib")

    # 2. Save the label encoders (already done, just confirming)
    print(f"Label encoder saved to: label_encoder.joblib")
    
    # 3. Save just the core classifier model for SHAP explanations
    core_classifier = best_model.named_steps['classifier']
    joblib.dump(core_classifier, 'student_risk_classifier_tuned.joblib')
    print(f"Core classification model saved to: student_risk_classifier_tuned.joblib")

if __name__ == '__main__':
    train_model()