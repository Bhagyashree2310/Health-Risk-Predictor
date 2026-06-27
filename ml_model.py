import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

# Define the clinical features
NUMERICAL_FEATURES = [
    'age', 'height', 'weight', 'bmi', 
    'systolic_bp', 'diastolic_bp', 'glucose', 'cholesterol'
]
CATEGORICAL_FEATURES = [
    'gender', 'smoking_status', 'alcohol_consumption', 
    'physical_activity', 'family_history'
]
ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI given weight in kg and height in cm."""
    if not height_cm or height_cm <= 0:
        return 0
    return round(weight_kg / ((height_cm / 100) ** 2), 1)

def generate_synthetic_data(num_samples=2500, random_seed=42):
    """Generate a synthetic dataset with realistic medical correlations."""
    np.random.seed(random_seed)
    
    # Generate random features
    age = np.random.randint(18, 85, size=num_samples)
    gender = np.random.choice(['Male', 'Female', 'Other'], size=num_samples, p=[0.48, 0.49, 0.03])
    height = np.random.normal(170, 10, size=num_samples) # cm
    # Weight linked to height and noise
    bmi_base = np.random.normal(26, 6, size=num_samples)
    bmi_base = np.clip(bmi_base, 15, 50)
    weight = bmi_base * ((height / 100) ** 2)
    
    # Blood pressure (correlated with age, bmi, and stress/genetics)
    sys_base = 110 + 0.3 * age + 0.8 * bmi_base + np.random.normal(0, 12, size=num_samples)
    systolic_bp = np.clip(sys_base, 85, 210).astype(int)
    
    dia_base = 70 + 0.15 * age + 0.4 * bmi_base + np.random.normal(0, 8, size=num_samples)
    diastolic_bp = np.clip(dia_base, 55, 125).astype(int)
    
    # Glucose (correlated with age and bmi)
    glucose_base = 75 + 0.2 * age + 0.9 * bmi_base + np.random.normal(0, 25, size=num_samples)
    # Add a separate spike for diabetic cases
    diabetic_spike = np.random.choice([0, 80], size=num_samples, p=[0.90, 0.10])
    glucose = np.clip(glucose_base + diabetic_spike, 65, 350).astype(int)
    
    # Cholesterol (correlated with age, bmi, and diet)
    chol_base = 150 + 0.6 * age + 1.2 * bmi_base + np.random.normal(0, 35, size=num_samples)
    cholesterol = np.clip(chol_base, 100, 420).astype(int)
    
    # Lifestyles
    smoking_status = np.random.choice(['Smoker', 'Non-Smoker'], size=num_samples, p=[0.20, 0.80])
    alcohol_consumption = np.random.choice(['None', 'Moderate', 'Heavy'], size=num_samples, p=[0.40, 0.45, 0.15])
    physical_activity = np.random.choice(['Low', 'Moderate', 'High'], size=num_samples, p=[0.35, 0.45, 0.20])
    family_history = np.random.choice(['Yes', 'No'], size=num_samples, p=[0.30, 0.70])
    
    # Compute clinical BMI
    bmi = np.round(weight / ((height / 100) ** 2), 1)
    
    # Build DataFrame
    df = pd.DataFrame({
        'age': age,
        'gender': gender,
        'height': np.round(height, 1),
        'weight': np.round(weight, 1),
        'bmi': bmi,
        'systolic_bp': systolic_bp,
        'diastolic_bp': diastolic_bp,
        'glucose': glucose,
        'cholesterol': cholesterol,
        'smoking_status': smoking_status,
        'alcohol_consumption': alcohol_consumption,
        'physical_activity': physical_activity,
        'family_history': family_history
    })
    
    # Clinical risk score calculation (to create realistic labels)
    # Base risk starts at 10%
    risk_points = 10.0
    
    # Age: older increases risk
    risk_points += (df['age'] - 18) / 67.0 * 15.0
    
    # BMI: >25 (overweight) +5, >30 (obese) +15, >35 (morbidly obese) +25
    risk_points += np.where(df['bmi'] > 35, 25.0, np.where(df['bmi'] > 30, 15.0, np.where(df['bmi'] > 25, 5.0, 0.0)))
    
    # Blood pressure: Hypertension > 140/90
    bp_risk = np.where((df['systolic_bp'] >= 140) | (df['diastolic_bp'] >= 90), 20.0, 
                       np.where((df['systolic_bp'] >= 130) | (df['diastolic_bp'] >= 80), 8.0, 0.0))
    risk_points += bp_risk
    
    # Glucose: Diabetic > 126 (+25), Pre-diabetic 100-125 (+10)
    glucose_risk = np.where(df['glucose'] >= 126, 25.0, np.where(df['glucose'] >= 100, 10.0, 0.0))
    risk_points += glucose_risk
    
    # Cholesterol: Hypercholesterolemia > 240 (+15), Borderline 200-239 (+5)
    chol_risk = np.where(df['cholesterol'] >= 240, 15.0, np.where(df['cholesterol'] >= 200, 5.0, 0.0))
    risk_points += chol_risk
    
    # Smoking: Smoker (+15)
    risk_points += np.where(df['smoking_status'] == 'Smoker', 15.0, 0.0)
    
    # Alcohol: Heavy (+10)
    risk_points += np.where(df['alcohol_consumption'] == 'Heavy', 10.0, 0.0)
    
    # Physical activity: Low (+10), High (-5)
    risk_points += np.where(df['physical_activity'] == 'Low', 10.0, np.where(df['physical_activity'] == 'High', -5.0, 0.0))
    
    # Family history (+12)
    risk_points += np.where(df['family_history'] == 'Yes', 12.0, 0.0)
    
    # Add random biological variance/noise (-10 to +10)
    noise = np.random.normal(0, 6, size=num_samples)
    final_score = np.clip(risk_points + noise, 0, 100)
    
    # Label mapping
    # Low Risk: < 35%
    # Moderate Risk: 35% to 65%
    # High Risk: >= 65%
    risk_category = np.where(final_score < 35, 'Low Risk', np.where(final_score < 65, 'Moderate Risk', 'High Risk'))
    
    df['risk_score_true'] = final_score
    df['risk_category'] = risk_category
    
    return df

def train_and_save_model(model_path='model.joblib'):
    """Generate synthetic data, train the machine learning pipeline, and save it."""
    print("Generating synthetic healthcare data...")
    df = generate_synthetic_data(num_samples=3000)
    
    X = df[ALL_FEATURES]
    y = df['risk_category']
    
    # Preprocessor using ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), NUMERICAL_FEATURES),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES)
        ]
    )
    
    # Random Forest Classifier
    rf_classifier = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        class_weight='balanced'
    )
    
    # Pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', rf_classifier)
    ])
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Training Random Forest Classifier...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    train_acc = pipeline.score(X_train, y_train)
    test_acc = pipeline.score(X_test, y_test)
    print(f"Training Accuracy: {train_acc:.2%}")
    print(f"Testing Accuracy: {test_acc:.2%}")
    
    # Compute global feature importances
    # Get feature names from preprocessor
    num_feature_names = NUMERICAL_FEATURES
    cat_transformer = preprocessor.named_transformers_['cat']
    cat_feature_names = cat_transformer.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    all_encoded_features = num_feature_names + cat_feature_names
    
    importances = rf_classifier.feature_importances_
    
    # Map importances back to raw feature groups for general dashboard display
    raw_importances = {}
    for raw_f in ALL_FEATURES:
        raw_importances[raw_f] = 0.0
        
    for encoded_name, imp in zip(all_encoded_features, importances):
        for raw_f in ALL_FEATURES:
            if encoded_name == raw_f or encoded_name.startswith(raw_f + '_'):
                raw_importances[raw_f] += imp
                break
                
    # Normalize raw importances to sum to 1.0
    total_imp = sum(raw_importances.values())
    for raw_f in raw_importances:
        raw_importances[raw_f] = raw_importances[raw_f] / total_imp
        
    # Pack model, metadata and save
    model_data = {
        'pipeline': pipeline,
        'global_importances': raw_importances,
        'features': ALL_FEATURES,
        'numerical_features': NUMERICAL_FEATURES,
        'categorical_features': CATEGORICAL_FEATURES
    }
    
    joblib.dump(model_data, model_path)
    print(f"Model saved successfully to {model_path}")
    return model_data

def load_model(model_path='model.joblib'):
    """Load the model. If it doesn't exist, train a new one first."""
    if not os.path.exists(model_path):
        # Ensure target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
        return train_and_save_model(model_path)
    return joblib.load(model_path)

def predict_patient_risk(patient_dict, model_data):
    """
    Predict risk parameters for a patient dictionary.
    Returns:
    - risk_category: 'Low Risk', 'Moderate Risk', 'High Risk'
    - risk_score: 0% - 100% continuous
    - confidence_score: prediction confidence of the predicted category (0.0 to 1.0)
    """
    pipeline = model_data['pipeline']
    
    # Create single-row DataFrame
    patient_df = pd.DataFrame([patient_dict])
    
    # Ensure all features exist in correct order
    for col in ALL_FEATURES:
        if col not in patient_df.columns:
            patient_df[col] = 0 if col in NUMERICAL_FEATURES else 'No'
            
    patient_df = patient_df[ALL_FEATURES]
    
    # Predict probabilities
    classes = pipeline.classes_
    probs = pipeline.predict_proba(patient_df)[0]
    
    prob_dict = dict(zip(classes, probs))
    
    p_low = prob_dict.get('Low Risk', 0.0)
    p_mod = prob_dict.get('Moderate Risk', 0.0)
    p_high = prob_dict.get('High Risk', 0.0)
    
    # Risk Score: linear combination of probability weights
    risk_score = p_mod * 50.0 + p_high * 100.0
    
    # Predicted Category
    pred_category = pipeline.predict(patient_df)[0]
    
    # Confidence Score is the probability of the predicted category
    confidence_score = prob_dict.get(pred_category, 0.0)
    
    return pred_category, round(risk_score, 1), round(confidence_score, 3)

def explain_local_risk(patient_dict, model_data):
    """
    Explain a single patient prediction using local feature perturbation.
    For each feature, we replace it with a 'healthy baseline' value and measure
    the drop in Risk Score.
    """
    # Baseline normal values
    baseline = {
        'age': 35,
        'gender': 'Female',
        'height': 168.0,
        'weight': 62.0, # BMI ~ 22.0
        'bmi': 22.0,
        'systolic_bp': 115,
        'diastolic_bp': 75,
        'glucose': 85,
        'cholesterol': 170,
        'smoking_status': 'Non-Smoker',
        'alcohol_consumption': 'None',
        'physical_activity': 'High',
        'family_history': 'No'
    }
    
    # Get original risk
    orig_cat, orig_score, orig_conf = predict_patient_risk(patient_dict, model_data)
    
    contributions = {}
    
    for f in ALL_FEATURES:
        # Check if the feature actually differs from baseline
        # (if it matches baseline, it doesn't contribute negatively to raising risk)
        val_patient = patient_dict.get(f)
        val_base = baseline.get(f)
        
        # Create perturbed patient dict where feature f is replaced with baseline
        perturbed_dict = patient_dict.copy()
        perturbed_dict[f] = val_base
        
        # Recalculate BMI if changing height or weight
        if f == 'height' or f == 'weight':
            perturbed_dict['bmi'] = calculate_bmi(perturbed_dict['weight'], perturbed_dict['height'])
            
        _, perturbed_score, _ = predict_patient_risk(perturbed_dict, model_data)
        
        # Contribution of this feature to raising risk
        # (if original risk is higher than when we set this feature to baseline,
        # then this feature increased the risk)
        diff = orig_score - perturbed_score
        contributions[f] = diff
        
    # Adjust BMI and height/weight correlations:
    # If height/weight are perturbed, their contribution should combine with BMI or be handled cleanly.
    # To keep features human-readable, we combine height and weight into 'BMI / Weight Status'
    if 'bmi' in contributions:
        contributions['bmi'] = max(contributions['bmi'], contributions.get('weight', 0.0))
        
    # Clean up and normalize results
    explanations = []
    
    # Dictionary mapping variable names to human-readable terms
    feature_labels = {
        'age': 'Age',
        'bmi': 'Elevated BMI',
        'systolic_bp': 'Elevated Systolic BP',
        'diastolic_bp': 'Elevated Diastolic BP',
        'glucose': 'High Blood Glucose',
        'cholesterol': 'High Cholesterol',
        'smoking_status': 'Smoking Status',
        'alcohol_consumption': 'Alcohol Consumption',
        'physical_activity': 'Lack of Physical Activity',
        'family_history': 'Family Medical History'
    }
    
    for f, contrib in contributions.items():
        if f in ['height', 'weight']:
            continue # Height/weight represented by BMI
        label = feature_labels.get(f, f)
        
        # Only report features that actively increase risk score by a positive threshold
        if contrib > 0.5:
            explanations.append({
                'feature': f,
                'label': label,
                'contribution': round(contrib, 2),
                'value': patient_dict.get(f)
            })
            
    # Sort by contribution descending
    explanations = sorted(explanations, key=lambda x: x['contribution'], reverse=True)
    return explanations

if __name__ == '__main__':
    # Train model locally when script is executed
    train_and_save_model()
